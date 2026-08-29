import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import { mkdtemp, mkdir, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

import { createCatalogChangeFeed, createRunsApiHandler, RunsApiError } from "../scripts/runs-api.mjs";
import { configuredExternalMediaSources } from "../vite.config.mjs";
import {
  attemptOutcome,
  generationTypeOf,
  outputState,
  projectShotRows,
  shotForAttempt,
} from "../src/run-detail-contract.js";
import {
  attachRunsMediaIndex,
  externalEvidenceFilterOptions,
  externalEvidenceState,
  externalDisplayMetadata,
  externalSourceOptions,
  externalGroupTitle,
  externalMediaUrl,
  externalReferenceUrl,
  externalStatus,
  externalStoryboardShots,
  groupMatchesEvidenceFilter,
  groupMatchesQuery,
  groupMatchesSource,
  preferredExternalGroup,
  preferredExternalLocation,
  readExternalCatalogResponse,
  runsMediaContextNotice,
} from "../src/external-media-contract.js";
import {
  enableMediaSound,
  mediaHasAudioTrack,
} from "../src/media-player-contract.js";
import {
  createLatestRequestGuard,
  createWorkspaceSelectionGuard,
  libraryLiveStatus,
} from "../src/library-refresh-contract.js";
import { formatShotTimecode, shotTiming } from "../src/shot-time-contract.js";
import {
  resolveVideoSourceSelection,
  videoSourceIsRefreshing,
  videoSourceSelectionValue,
} from "../src/video-library-source-contract.js";

test("video source selection stays directory-level while Runs workspace selection stays below it", () => {
  const runsCatalog = [
    { workspace: "run-a/project.yaml", run_id: "run-a" },
    { workspace: "run-b/manifest.json", run_id: "run-b" },
  ];

  assert.equal(videoSourceSelectionValue("all", "run-a/project.yaml"), "all");
  assert.equal(videoSourceSelectionValue("runs", "run-a/project.yaml"), "runs");
  assert.deepEqual(resolveVideoSourceSelection("runs", runsCatalog), {
    sourceId: "runs",
    workspace: null,
  });
  assert.deepEqual(resolveVideoSourceSelection("comfyui-output", runsCatalog), {
    sourceId: "comfyui-output",
    workspace: null,
  });
  assert.deepEqual(resolveVideoSourceSelection("runs-workspace:missing/project.yaml", runsCatalog), {
    sourceId: "runs",
    workspace: null,
  });
  assert.equal(videoSourceIsRefreshing("runs", false, true), false);
  assert.equal(videoSourceIsRefreshing("all", false, true), true);
  assert.equal(videoSourceIsRefreshing("comfyui-output", true, false), false);
});

test("video library rail renders one unified source selector", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    const { VideoLibraryRail } = await server.ssrLoadModule("/src/video-library-rail.jsx");
    const markup = renderToStaticMarkup(React.createElement(VideoLibraryRail, {
      runsCatalog: [{ workspace: "run-a/shot-01/production/project.yaml", run_id: "run-a", kind: "production" }],
      workspace: "run-a/shot-01/production/project.yaml",
      attempts: [],
      selectedId: "",
      runsLoading: false,
      runsError: "",
      externalCatalog: {
        sources: [{ id: "comfyui-output", label: "ComfyUI Output", status: "available" }],
        groups: [],
      },
      selectedSha: "",
      selectedSource: "all",
      query: "",
      externalLoading: false,
      externalError: "",
      activeSurface: "runs",
      liveStatus: "live",
      onWorkspace() {},
      onSelectAttempt() {},
      onSelectExternal() {},
      onSource() {},
      onQuery() {},
      onRefresh() {},
    }));

    assert.equal((markup.match(/id="video-source-select"/g) || []).length, 1);
    assert.match(markup, /id="video-source-select"/);
    assert.match(markup, /<optgroup label="视频目录">/);
    assert.match(markup, /<option value="all"[^>]*>全部视频来源<\/option>/);
    assert.match(markup, /<option value="runs"[^>]*>Runs<\/option>/);
    assert.match(markup, /<option value="comfyui-output"[^>]*>ComfyUI Output<\/option>/);
    const sourceSelector = markup.match(/<select id="video-source-select"[\s\S]*?<\/select>/)?.[0] || "";
    assert.doesNotMatch(sourceSelector, /run-a|shot-01|project\.yaml|runs-workspace:/);
    assert.doesNotMatch(sourceSelector, /全部视频来源 ·|ComfyUI Output ·/);
    assert.doesNotMatch(markup, /workspace-select|workspace-picker/);

    const staleMarkup = renderToStaticMarkup(React.createElement(VideoLibraryRail, {
      runsCatalog: [{ workspace: "run-b/project.yaml", run_id: "run-b" }],
      workspace: "run-a/project.yaml",
      attempts: [],
      selectedId: "",
      runsLoading: false,
      runsError: "工作区不存在",
      externalCatalog: { sources: [], groups: [] },
      selectedSha: "",
      selectedSource: "runs",
      query: "",
      externalLoading: false,
      externalError: "",
      activeSurface: "runs",
      liveStatus: "live",
      onWorkspace() {},
      onSelectAttempt() {},
      onSelectExternal() {},
      onSource() {},
      onQuery() {},
      onRefresh() {},
    }));
    assert.match(staleMarkup, /<option value="runs"[^>]*selected="">Runs<\/option>/);
    assert.doesNotMatch(staleMarkup.match(/<select id="video-source-select"[\s\S]*?<\/select>/)?.[0] || "", /project\.yaml|当前不可用/);
    assert.equal((staleMarkup.match(/<select/g) || []).length, 1);

    const runsMarkup = renderToStaticMarkup(React.createElement(VideoLibraryRail, {
      runsCatalog: [
        { workspace: "run-a/shot-01/production/project.yaml", run_id: "run-a", kind: "production" },
        { workspace: "run-b/manifest.json", run_id: "run-b", kind: "legacy" },
      ],
      workspace: "run-a/shot-01/production/project.yaml",
      attempts: [],
      selectedId: "",
      runsLoading: false,
      runsError: "",
      externalCatalog: { sources: [], groups: [] },
      selectedSha: "",
      selectedSource: "runs",
      query: "",
      externalLoading: false,
      externalError: "",
      activeSurface: "runs",
      liveStatus: "live",
      onWorkspace() {},
      onSelectAttempt() {},
      onSelectExternal() {},
      onSource() {},
      onQuery() {},
      onRefresh() {},
    }));
    assert.match(runsMarkup, /RUNS · 当前工作区/);
    assert.match(runsMarkup, />run-a<\/strong>/);
    assert.match(runsMarkup, />shot-01\/production\/project\.yaml<\/span>/);
    assert.match(runsMarkup, /RUNS · 其他工作区/);
    assert.match(runsMarkup, />run-b<\/strong>/);
    assert.match(runsMarkup, />manifest\.json<\/span>/);
  } finally {
    await server.close();
  }
});

test("video library rail labels and filters External evidence states without N/E", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    const { VideoLibraryRail } = await server.ssrLoadModule("/src/video-library-rail.jsx");
    const markup = renderToStaticMarkup(React.createElement(VideoLibraryRail, {
      runsCatalog: [],
      workspace: "",
      attempts: [],
      selectedId: "",
      runsLoading: false,
      runsError: "",
      externalCatalog: {
        sources: [{ id: "comfyui-output", label: "ComfyUI Output", status: "available" }],
        groups: [
          {
            sha256: "a".repeat(64),
            bytes: 100,
            locations: [{ source_id: "comfyui-output", file_name: "linked.mp4", token: "external_linked" }],
            run_bindings: [{
              target_shot_id: "shot-linked",
              generation_type: "T2V",
              prompt_text: "Exact Runs prompt",
              shot_snapshot_status: "unavailable",
            }],
          },
          {
            sha256: "b".repeat(64),
            bytes: 101,
            locations: [{ source_id: "comfyui-output", file_name: "incomplete.mp4", token: "external_incomplete" }],
            evidence_refs: [{ relative_path: "result.json" }],
          },
          {
            sha256: "c".repeat(64),
            bytes: 102,
            locations: [{ source_id: "comfyui-output", file_name: "unbound.mp4", token: "external_unbound" }],
          },
        ],
      },
      selectedSha: "",
      selectedSource: "comfyui-output",
      query: "",
      externalLoading: false,
      externalError: "",
      runsContextLoading: false,
      runsContextError: "",
      activeSurface: "external",
      liveStatus: "live",
      onWorkspace() {},
      onSelectAttempt() {},
      onSelectExternal() {},
      onSource() {},
      onQuery() {},
      onRefresh() {},
    }));

    assert.match(markup, /id="external-evidence-filter"/);
    assert.match(markup, /已关联 \(1\)/);
    assert.match(markup, /Runs 待恢复 \(0\)/);
    assert.match(markup, /旁证待解析 \(1\)/);
    assert.match(markup, /无绑定证据 \(1\)/);
    assert.match(markup, /<option value="linked" selected="">已关联 \(1\)<\/option>/);
    assert.match(markup, />Runs 已关联<\/span>/);
    assert.doesNotMatch(markup, />旁证待解析<\/span>/);
    assert.doesNotMatch(markup, />无绑定证据<\/span>/);
    assert.match(markup, /shot-linked · T2V/);
    assert.match(markup, /Exact Runs prompt/);
    assert.doesNotMatch(markup, />N\/E<\/span>/);
  } finally {
    await server.close();
  }
});

test("Runs attempt keeps the inline player and Project Shot breakdown in the main detail row", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    const { RunsAttemptView, RunsWorkspaceView } = await server.ssrLoadModule("/src/App.jsx");
    assert.equal(typeof RunsAttemptView, "function");
    assert.equal(typeof RunsWorkspaceView, "function");
    const attempt = {
      attempt_id: "attempt-inline-video",
      status: "running",
      phase: "validate",
      mode: "text_to_video",
      target_shot_id: "shot-1",
      prompt_text: "sealed prompt",
      fetched_media: {
        token: "fetched-video-token",
        mime_type: "video/mp4",
        bytes: 1234,
        source_kind: "fetched_evidence",
      },
    };
    const detail = {
      workspace: "demo/project.yaml",
      manifest: { revision: 1 },
      project: { title: "Demo" },
      shots: [{ shot_id: "shot-1", intent: "Show the result", revision: 1 }],
      attempts: [attempt],
    };
    const markup = renderToStaticMarkup(React.createElement(RunsAttemptView, {
      detail,
      attempt,
      selectedAttemptId: attempt.attempt_id,
      onSelectAttempt() {},
      onEvidence() {},
      continuityContent: null,
    }));

    assert.match(markup, /<video[^>]+src="\/api\/runs\/media\/fetched-video-token"[^>]*controls/);
    assert.match(markup, /<div class="readiness-pane">[\s\S]*<section class="shot-breakdown"[\s\S]*<\/div><aside class="detail-aside">/);
    assert.doesNotMatch(markup, /<section class="action-bar">[\s\S]*<section class="shot-breakdown"/);

    const workspaceMarkup = renderToStaticMarkup(React.createElement(RunsWorkspaceView, {
      detail: { ...detail, attempts: [] },
      selectedAttemptId: "",
      onSelectAttempt() {},
    }));
    assert.match(workspaceMarkup, /<section class="workspace-overview">[\s\S]*<section class="shot-breakdown"/);
    assert.doesNotMatch(workspaceMarkup, /<section class="action-bar workspace-action-bar">[\s\S]*<section class="shot-breakdown"/);
  } finally {
    await server.close();
  }
});

test("default external media sources include the AI-VIDEO experiments directory", () => {
  assert.deepEqual(configuredExternalMediaSources({ repoRoot: "/repo", homeRoot: "/home/operator" }), [
    { id: "artifacts", label: "AI-VIDEO Artifacts", kind: "development_artifact", root: "/repo/artifacts" },
    { id: "ai-video-experiments", label: "AI-VIDEO Experiments", kind: "development_artifact", root: "/home/operator/ai-video-experiments" },
    { id: "comfyui-output", label: "ComfyUI Output", kind: "raw_provider_output", root: "/home/operator/ComfyUI/output" },
    { id: "qingyan-project", label: "青颜项目目录", kind: "external_project_asset", root: "/home/operator/电商图片/青颜" },
  ]);
});

test("Shot timing distinguishes exact clip ranges from planned duration and missing timeline position", () => {
  assert.deepEqual(shotTiming({
    start_seconds: 0,
    end_seconds: 5.1666666667,
    duration_seconds: 5.1666666667,
    timing_basis: "exact_output_clip",
  }), {
    evaluated: true,
    label: "视频内时间",
    value: "00:00.000 – 00:05.167 · 5.167s",
  });
  assert.deepEqual(shotTiming({ duration_policy: { mode: "fixed", seconds: 4 } }), {
    evaluated: true,
    label: "计划时长",
    value: "4s · 成片位置 NOT_EVALUATED",
  });
  assert.deepEqual(shotTiming({ duration_policy: { minimum_seconds: 2.1, maximum_seconds: 3 } }), {
    evaluated: true,
    label: "计划时长范围",
    value: "2.1s – 3s · 成片位置 NOT_EVALUATED",
  });
  assert.deepEqual(shotTiming({ start_seconds: 5, end_seconds: 4 }), {
    evaluated: false,
    label: "时间",
    value: "NOT_EVALUATED",
  });
  assert.deepEqual(shotTiming({ start_seconds: 0, end_seconds: 5, duration_seconds: 10 }), {
    evaluated: false,
    label: "时间",
    value: "NOT_EVALUATED",
  });
  assert.equal(formatShotTimecode(3_661.25), "01:01:01.250");
});

test("run detail contract keeps lifecycle outcome separate from phase and media", () => {
  assert.deepEqual(attemptOutcome({ status: "succeeded", phase: "activate" }), {
    key: "succeeded", label: "成功", tone: "ready", terminal: true,
  });
  assert.deepEqual(attemptOutcome({ status: "failed", phase: "validate" }), {
    key: "failed", label: "失败", tone: "blocked", terminal: true,
  });
  assert.deepEqual(attemptOutcome({ status: "interrupted", phase: "fetch" }), {
    key: "interrupted", label: "已中断", tone: "interrupted", terminal: true,
  });
  assert.deepEqual(attemptOutcome({ status: "outcome_unknown", phase: "submitted" }), {
    key: "outcome_unknown", label: "结果未知", tone: "unknown", terminal: true,
  });
  assert.deepEqual(attemptOutcome({ status: "running", phase: "validate" }), {
    key: "running", label: "进行中", tone: "gated", terminal: false,
  });

  assert.deepEqual(outputState({ status: "failed", phase: "validate" }), {
    key: "missing_after_failure", label: "失败，未登记可播放视频", tone: "blocked",
  });
  assert.deepEqual(outputState({ status: "interrupted", phase: "fetch" }), {
    key: "missing_after_failure", label: "已中断，未登记可播放视频", tone: "interrupted",
  });
  assert.deepEqual(outputState({ status: "failed", phase: "validate", fetched_media: { token: "fetched" } }), {
    key: "fetched_evidence", label: "已获取视频，尚未成为 candidate", tone: "blocked",
  });
  assert.deepEqual(outputState({ status: "succeeded", phase: "activate", candidate_media: { token: "candidate" } }), {
    key: "registered_candidate", label: "Candidate 已注册", tone: "ready",
  });
  assert.deepEqual(outputState({ status: "succeeded", phase: "activate" }), {
    key: "missing_after_success", label: "成功记录缺少已注册输出", tone: "gated",
  });
});

test("external selection prefers exact Shot evidence over an unbound newest video", () => {
  const unbound = { sha256: "a".repeat(64), locations: [{ relative_path: "newest.mp4" }] };
  const promptBound = {
    sha256: "b".repeat(64),
    shot_id: "shot-1",
    prompt_text: "exact prompt",
    locations: [{ relative_path: "shot-1.mp4" }],
  };
  const composition = {
    sha256: "c".repeat(64),
    composition: { ordered_shots: [{ shot_id: "shot-1" }, { shot_id: "shot-2" }] },
    locations: [{ relative_path: "final.mp4" }],
  };

  assert.equal(preferredExternalGroup([unbound, promptBound]), promptBound);
  assert.equal(preferredExternalGroup([unbound, promptBound, composition]), composition);
  assert.equal(preferredExternalGroup([]), null);
});

test("external storyboard falls back to exact Shot prompt when composition is empty", () => {
  const group = {
    shot_id: "shot-1",
    prompt_text: "exact prompt",
    generation_type: "FL2VA",
    reported_status: "completed",
    composition: { ordered_shots: [] },
  };

  assert.deepEqual(externalStoryboardShots(group), [{
    shot_id: "shot-1",
    prompt_text: "exact prompt",
    shot_type: undefined,
    generation_type: "FL2VA",
    reported_status: "completed",
  }]);
});

test("external experiment evidence keeps Shot, references, prompt, and result layers together", () => {
  const shotEvidence = {
    entity_kind: "shot",
    association_status: "verified_experiment_result_chain",
    shot_id: "m6-shot-b",
    intent: "女孩接过产品，老人穿过门离开。",
    prompt_text: "sealed exact prompt",
    generation_type: "image_to_video",
    generation_result: "OUTPUT_RECORDED",
    technical_gate: "PASS",
    human_verdict: "NOT_EVALUATED",
    reference_inputs: [{
      role: "first_frame",
      asset_id: "anchor-first",
      sha256: "b".repeat(64),
      token: "external_ai-video-experiments_reference_first",
    }],
    findings: [{ requirement_id: "causal_state", verdict: "PASS", evidence: "handoff visible" }],
  };
  const group = {
    status: "NOT_EVALUATED",
    reported_status: "OUTPUT_RECORDED",
    shot_evidence: [shotEvidence],
    locations: [{ relative_path: "outputs/shot-b.mp4" }],
  };

  assert.deepEqual(externalStoryboardShots(group), [shotEvidence]);
  assert.equal(externalReferenceUrl(shotEvidence.reference_inputs[0]), "/api/external-media/media/external_ai-video-experiments_reference_first");
  assert.equal(externalReferenceUrl({ token: "../../escape" }), null);
  assert.equal(externalStatus(group).tone, "ready");
  assert.equal(groupMatchesQuery(group, "handoff visible"), true);
  assert.equal(groupMatchesQuery(group, "anchor-first"), true);
});

test("external reference previews load eagerly inside the nested detail scroller", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    const { ExternalShotBreakdown } = await server.ssrLoadModule("/src/shot-breakdown.jsx");
    const { ExternalMediaDetail } = await server.ssrLoadModule("/src/App.jsx");
    const markup = renderToStaticMarkup(React.createElement(ExternalShotBreakdown, {
      group: {
        reported_status: "OUTPUT_RECORDED",
        shot_evidence: [{
          shot_id: "shot-b",
          reference_inputs: [{
            role: "first_frame",
            asset_id: "anchor-first",
            sha256: "b".repeat(64),
            token: "external_ai-video-experiments_reference_first",
          }],
        }],
      },
    }));
    const referenceImage = markup.match(/<img[^>]+external_ai-video-experiments_reference_first[^>]*>/)?.[0] || "";
    assert.match(referenceImage, /src="\/api\/external-media\/media\/external_ai-video-experiments_reference_first"/);
    assert.match(referenceImage, /loading="eager"/);
    assert.doesNotMatch(markup, /loading="lazy"/);

    const boundMetadataGroup = {
      sha256: "a".repeat(64),
      token: "external_raw_exact",
      status: "NOT_EVALUATED",
      metadata_status: "bound",
      prompt_text: "Exact embedded Prompt.",
      shot_type: "long_video_segment",
      evidence_refs: [{ source_id: "raw", relative_path: "manifest.json" }],
      locations: [{ source_id: "raw", source_label: "Raw", relative_path: "segment.mp4", file_name: "segment.mp4" }],
    };
    const emptyShotMarkup = renderToStaticMarkup(React.createElement(ExternalShotBreakdown, { group: boundMetadataGroup }));
    assert.match(emptyShotMarkup, /已有 exact-bound Prompt 或类型/);
    assert.doesNotMatch(emptyShotMarkup, /不会从文件名或目录猜测脚本与 Prompt/);

    const detailMarkup = renderToStaticMarkup(React.createElement(ExternalMediaDetail, {
      group: boundMetadataGroup,
      sources: [{ id: "raw", label: "Raw" }],
    }));
    assert.match(detailMarkup, /Prompt 或类型来自受支持且与 exact bytes 绑定的 metadata/);
    assert.match(detailMarkup, /Exact embedded Prompt/);
    assert.doesNotMatch(detailMarkup, /没有找到语义受支持且与 exact bytes 绑定的生成记录/);
  } finally {
    await server.close();
  }
});

test("external Runs detail labels Prompt separately when the structured Shot snapshot is unavailable", async () => {
  const server = await createServer({
    root: fileURLToPath(new URL("..", import.meta.url)),
    server: { middlewareMode: true },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    const { ExternalShotBreakdown } = await server.ssrLoadModule("/src/shot-breakdown.jsx");
    const markup = renderToStaticMarkup(React.createElement(ExternalShotBreakdown, {
      group: {
        run_bindings: [{
          target_shot_id: "shot-unavailable",
          generation_type: "T2V",
          prompt_text: "Exact submitted Prompt.",
          shot_snapshot_status: "unavailable",
          shot_snapshot: null,
        }],
      },
    }));

    assert.match(markup, /structured Shot snapshot 不可用/);
    assert.match(markup, />实际提交 Prompt<\/span>/);
    assert.match(markup, /Exact submitted Prompt/);
    assert.doesNotMatch(markup, /分镜脚本参考/);
  } finally {
    await server.close();
  }
});

test("external experiment ambiguity stays fail-closed and visible", () => {
  const status = externalStatus({
    association_ambiguity: true,
    reported_status: "OUTPUT_RECORDED",
    shot_evidence: [],
  });

  assert.deepEqual(status, {
    raw: "AMBIGUOUS_EXPERIMENT_EVIDENCE",
    label: "证据关联冲突",
    badge: "证据冲突",
    tone: "blocked",
    evaluated: false,
    evidence_state: "conflict",
    ambiguous: true,
  });
});

test("workspace selection guard rejects a late refresh commit", async () => {
  const guard = createWorkspaceSelectionGuard();
  const refreshToken = guard.snapshot();
  let releaseRefresh;
  const delayedRefresh = new Promise((resolve) => { releaseRefresh = resolve; });
  const state = { workspace: "old" };
  const refresh = delayedRefresh.then(() => {
    if (guard.canCommit(refreshToken)) state.workspace = "old-refresh";
  });

  const selectionToken = guard.beginSelection();
  state.workspace = "new-selection";
  releaseRefresh();
  await refresh;

  assert.equal(guard.canCommit(refreshToken), false);
  assert.equal(guard.canCommit(selectionToken), true);
  assert.equal(state.workspace, "new-selection");
});

test("latest detail request guard rejects an older response for the same workspace", async () => {
  const guard = createLatestRequestGuard();
  const state = { revision: "initial" };
  let releaseOld;
  let releaseNew;
  const oldResponse = new Promise((resolve) => { releaseOld = resolve; });
  const newResponse = new Promise((resolve) => { releaseNew = resolve; });
  const oldToken = guard.beginRequest();
  const oldCommit = oldResponse.then(() => {
    if (guard.canCommit(oldToken)) state.revision = "old";
  });
  const newToken = guard.beginRequest();
  const newCommit = newResponse.then(() => {
    if (guard.canCommit(newToken)) state.revision = "new";
  });

  releaseNew();
  await newCommit;
  releaseOld();
  await oldCommit;

  assert.equal(guard.canCommit(oldToken), false);
  assert.equal(guard.canCommit(newToken), true);
  assert.equal(state.revision, "new");
});

test("live status reflects selected-source coverage and stale refreshes", () => {
  const connected = {
    connectionState: "connected",
    watchedSources: ["runs", "artifacts"],
    expectedSources: ["runs", "artifacts", "comfyui-output"],
  };
  assert.equal(libraryLiveStatus({ ...connected, selectedSource: "runs" }), "live");
  assert.equal(libraryLiveStatus({ ...connected, selectedSource: "comfyui-output" }), "unavailable");
  assert.equal(libraryLiveStatus({ ...connected, selectedSource: "all" }), "partial");
  assert.equal(libraryLiveStatus({ ...connected, selectedSource: "runs", refreshFailed: true }), "stale");
  assert.equal(libraryLiveStatus({ ...connected, selectedSource: "runs", connectionState: "reconnecting" }), "reconnecting");
});

test("run detail contract derives generation mode and exact-attempt Shot only", () => {
  const activeShot = {
    shot_id: "shot-1", revision: 4, content_hash: "active", intent: "active intent",
  };
  const historicalShot = {
    shot_id: "shot-1", revision: 3, content_hash: "sealed", intent: "historical intent",
  };
  const detail = { shots: [activeShot] };

  assert.equal(generationTypeOf({ mode: "text_to_video" }), "T2V");
  assert.equal(generationTypeOf({ mode: "reference_to_video" }), "R2V");
  assert.equal(generationTypeOf({
    mode: "image_to_video",
    input_bindings: [{ role: "first_frame" }, { role: "last_frame" }],
  }), "FL2V");
  assert.equal(generationTypeOf({ mode: "image_to_video", input_bindings: [{ role: "first_frame" }] }), "I2V");

  assert.deepEqual(shotForAttempt(detail, {
    target_shot_id: "shot-1",
    target_shot_revision: 3,
    target_shot_content_hash: "sealed",
    shot_snapshot_status: "verified",
    shot_snapshot: historicalShot,
  }), historicalShot);
  assert.deepEqual(shotForAttempt(detail, {
    target_shot_id: "shot-1",
    target_shot_revision: 3,
    target_shot_content_hash: "sealed",
    shot_snapshot_status: "unavailable",
  }), {
    shot_id: "shot-1",
    revision: 3,
    content_hash: "sealed",
    snapshot_available: false,
  });
  assert.deepEqual(shotForAttempt(detail, {
    shot_snapshot_status: "unavailable",
  }), { snapshot_available: false });
  assert.deepEqual(shotForAttempt(detail, {
    target_shot_id: "shot-1",
    shot_snapshot_status: "unavailable",
  }), {
    shot_id: "shot-1",
    snapshot_available: false,
  });
  assert.deepEqual(shotForAttempt(detail, {
    target_shot_id: "shot-1",
  }), activeShot);
});

test("project Shot rows keep Project order, all attempts, and unmatched evidence", () => {
  const detail = {
    shots: [
      { shot_id: "shot-2", intent: "second" },
      { shot_id: "shot-1", intent: "first" },
    ],
    attempts: [
      { attempt_id: "attempt-1a", target_shot_id: "shot-1" },
      { attempt_id: "attempt-orphan", target_shot_id: "shot-missing" },
      { attempt_id: "attempt-1b", target_shot_id: "shot-1" },
    ],
  };

  assert.deepEqual(projectShotRows(detail), {
    rows: [
      { shot: detail.shots[0], attempts: [] },
      { shot: detail.shots[1], attempts: [detail.attempts[0], detail.attempts[2]] },
    ],
    unmatched: [detail.attempts[1]],
  });
});

test("external media UI contract keeps non-canonical unknowns explicit", () => {
  const group = {
    sha256: "a".repeat(64),
    status: "NOT_EVALUATED",
    preview_token: "external_artifacts_preview",
    locations: [
      { source_id: "comfyui-output", relative_path: "raw/clip.mp4", file_name: "clip.mp4", token: "external_comfy_copy" },
      { source_id: "artifacts", relative_path: "runtime/shot.mp4", file_name: "shot.mp4", token: "external_artifacts_preview" },
    ],
  };

  assert.deepEqual(externalStatus(group), {
    raw: "NOT_EVALUATED",
    label: "没有与 exact bytes 绑定的证据",
    badge: "无绑定证据",
    tone: "unknown",
    evaluated: false,
    evidence_state: "unbound",
  });
  assert.equal(preferredExternalLocation(group).source_id, "artifacts");
  assert.equal(externalMediaUrl(group), "/api/external-media/media/external_artifacts_preview");
  assert.equal(externalGroupTitle(group), "shot.mp4");
  assert.equal(groupMatchesSource(group, "artifacts"), true);
  assert.equal(groupMatchesSource(group, "qingyan-project"), false);
  assert.equal(groupMatchesSource(group, "all"), true);
  assert.equal(groupMatchesQuery(group, "shot.mp4"), true);
  assert.equal(groupMatchesQuery({ ...group, shot_id: "shot-07", prompt_text: "yellow bottle" }, "YELLOW BOTTLE"), true);
  assert.equal(groupMatchesQuery({ ...group, composition: { ordered_shots: [{ shot_id: "shot-close", purpose: "产品收口", copy: ["抑汗净味"] }] } }, "产品收口"), true);
  assert.equal(groupMatchesQuery({ ...group, composition: { ordered_shots: [{ shot_id: "shot-close", purpose: "产品收口", copy: ["抑汗净味"] }] } }, "抑汗净味"), true);
  assert.equal(groupMatchesQuery(group, "missing"), false);
  assert.equal(externalStatus({ status: "succeeded" }).tone, "unknown");
  assert.equal(externalStatus({ status: "failed" }).tone, "unknown");
  assert.equal(externalStatus({ status: "NOT_EVALUATED", reported_status: "succeeded" }).tone, "ready");
  assert.equal(externalStatus({ status: "NOT_EVALUATED", reported_status: false }).tone, "blocked");
});

test("external evidence states distinguish linked, incomplete, and unbound groups", () => {
  const linked = { reported_status: "OUTPUT_RECORDED", evidence_refs: [{ relative_path: "receipt.json" }] };
  const incomplete = { evidence_refs: [{ relative_path: "result.json" }] };
  const unbound = { evidence_refs: [] };

  assert.equal(externalEvidenceState(linked), "linked");
  assert.equal(externalEvidenceState(incomplete), "unparsed");
  assert.equal(externalEvidenceState(unbound), "unbound");
  assert.deepEqual(externalStatus(incomplete), {
    raw: "UNPARSED_BOUND_EVIDENCE",
    label: "存在 exact-bound 旁证，但当前 schema 尚未支持",
    badge: "旁证待解析",
    tone: "gated",
    evaluated: false,
    evidence_state: "unparsed",
  });
  assert.equal(groupMatchesEvidenceFilter(linked, "linked"), true);
  assert.equal(groupMatchesEvidenceFilter(incomplete, "linked"), false);
  assert.equal(groupMatchesEvidenceFilter(unbound, "unbound"), true);
  assert.deepEqual(externalEvidenceFilterOptions([linked, incomplete, unbound]), [
    { id: "all", label: "全部证据状态", count: 3 },
    { id: "linked", label: "已关联", count: 1 },
    { id: "incomplete", label: "Runs 待恢复", count: 0 },
    { id: "unparsed", label: "旁证待解析", count: 1 },
    { id: "unbound", label: "无绑定证据", count: 1 },
  ]);
});

test("exact-bound metadata without a reported outcome is linked but not evaluated", () => {
  const status = externalStatus({
    metadata_status: "bound",
    evidence_refs: [{ relative_path: "work/external-media-metadata.json" }],
    reported_status: null,
  });

  assert.deepEqual(status, {
    raw: "NOT_EVALUATED",
    label: "Prompt、Shot 或类型已与 exact bytes 绑定；生成状态未评估",
    badge: "旁证已关联",
    tone: "interrupted",
    evaluated: false,
    evidence_state: "linked",
  });
});

test("Runs media context notice distinguishes identity coverage from global strict validity", () => {
  assert.equal(runsMediaContextNotice({ boundary: { complete: true } }), "");
  assert.match(runsMediaContextNotice({
    boundary: { complete: false, identity_coverage_complete: true },
    summary: { recovered_workspace_count: 3, failed_workspace_count: 2 },
  }), /3 个 workspace 恢复了封存视频证据，2 个 workspace 无法完整重开/);
  assert.match(runsMediaContextNotice({
    boundary: { complete: false, identity_coverage_complete: false },
    summary: { failed_workspace_count: 5 },
  }), /仅展示已确认的 exact match/);
});

test("external evidence reuses a semantically unambiguous exact Runs binding", () => {
  const runBinding = {
    workspace: "run-a/project.yaml",
    attempt_id: "attempt-a",
    target_shot_id: "shot-7",
    generation_type: "I2V",
    prompt_text: "Exact Runs prompt.",
    shot_snapshot_status: "verified",
    shot_snapshot: {
      shot_id: "shot-7",
      intent: "Reveal the product.",
      visual_strategy: "generated_video",
      revision: 2,
      content_hash: "b".repeat(64),
    },
  };
  const group = { run_bindings: [runBinding], evidence_refs: [] };

  assert.equal(externalEvidenceState(group), "linked");
  assert.deepEqual(externalDisplayMetadata(group), {
    shot_id: "shot-7",
    shot_type: null,
    generation_type: "I2V",
    prompt_text: "Exact Runs prompt.",
    run_binding: runBinding,
    source: "runs_exact_sha",
  });
  assert.deepEqual(externalStoryboardShots(group), [{
    ...runBinding.shot_snapshot,
    prompt_text: "Exact Runs prompt.",
    generation_type: "I2V",
    evidence_source: "runs_exact_sha",
    snapshot_available: true,
  }]);
  assert.equal(externalStatus(group).badge, "Runs 已关联");
});

test("conflicting Runs Shot bindings stay fail-closed even when External has a reported status", () => {
  const base = {
    target_shot_id: "shot-7",
    target_shot_revision: 1,
    target_shot_content_hash: "a".repeat(64),
    generation_type: "T2V",
    prompt_text: "Same prompt.",
    shot_snapshot_status: "unavailable",
  };
  const group = {
    reported_status: "OUTPUT_RECORDED",
    run_bindings: [base, {
      ...base,
      target_shot_revision: 2,
      target_shot_content_hash: "b".repeat(64),
    }],
  };

  assert.equal(externalStatus(group).badge, "Runs 关联冲突");
  assert.equal(externalStatus(group).evidence_state, "conflict");
  assert.equal(externalDisplayMetadata(group).run_binding, null);
  assert.deepEqual(externalStoryboardShots(group), []);
});

test("Runs media index joins External only on exact SHA and bytes", () => {
  const sha256 = "d".repeat(64);
  const binding = { sha256, bytes: 123, workspace: "run-a/project.yaml", attempt_id: "attempt-a" };
  const catalog = {
    groups: [
      { sha256, bytes: 123, reported_status: null },
      { sha256, bytes: 124, reported_status: null },
    ],
  };

  const joined = attachRunsMediaIndex(catalog, {
    boundary: { read_only: true, association: "exact_sha256_and_bytes", lifecycle_projection: false, complete: true },
    bindings: [binding],
  });

  assert.deepEqual(joined.groups[0].run_bindings, [binding]);
  assert.deepEqual(joined.groups[1].run_bindings, []);
  assert.equal(joined.groups[0].reported_status, null);
  assert.equal(joined.runs_media_context.association, "exact_sha256_and_bytes");

  const incomplete = attachRunsMediaIndex(catalog, {
    boundary: { read_only: true, association: "exact_sha256_and_bytes", lifecycle_projection: false, complete: false },
    bindings: [binding],
  });
  assert.deepEqual(incomplete.groups[0].run_bindings, [binding]);
  assert.equal(incomplete.groups[0].runs_context_complete, false);
  assert.equal(incomplete.groups[1].runs_context_complete, false);
  assert.equal(externalStatus(incomplete.groups[1]).raw, "INCOMPLETE_RUNS_CONTEXT");
  assert.equal(incomplete.runs_media_context.complete, false);

  const unresolvedSha = "e".repeat(64);
  const identityScoped = attachRunsMediaIndex({
    groups: [
      { sha256, bytes: 124, reported_status: null },
      { sha256: unresolvedSha, bytes: 456, reported_status: null },
    ],
  }, {
    boundary: {
      read_only: true,
      association: "exact_sha256_and_bytes",
      lifecycle_projection: false,
      complete: false,
      identity_coverage_complete: true,
    },
    bindings: [],
    unresolved_media: [{ sha256: unresolvedSha, bytes: 456 }],
  });
  assert.equal(identityScoped.groups[0].runs_context_complete, true);
  assert.equal(externalStatus(identityScoped.groups[0]).evidence_state, "unbound");
  assert.equal(identityScoped.groups[1].runs_context_complete, false);
  assert.equal(externalStatus(identityScoped.groups[1]).raw, "INCOMPLETE_RUNS_CONTEXT");

  const malformedCoverage = attachRunsMediaIndex(catalog, {
    boundary: {
      read_only: true,
      association: "exact_sha256_and_bytes",
      lifecycle_projection: false,
      complete: false,
      identity_coverage_complete: true,
    },
    bindings: [],
    unresolved_media: [{ sha256: "invalid", bytes: 1 }],
  });
  assert.equal(malformedCoverage.groups[0].runs_context_complete, false);

  const pending = attachRunsMediaIndex(catalog, null);
  assert.equal(pending.groups[0].runs_context_complete, false);
  assert.equal(pending.groups[1].runs_context_complete, false);
  assert.equal(externalStatus(pending.groups[0]).raw, "INCOMPLETE_RUNS_CONTEXT");
  assert.equal(externalStatus(pending.groups[1]).badge, "Runs 待恢复");
});

test("external source selector stays compact and defaults to all sources", () => {
  const catalog = {
    groups: [
      { locations: [{ source_id: "artifacts" }] },
      { locations: [{ source_id: "comfyui-output" }] },
      { locations: [{ source_id: "artifacts" }, { source_id: "comfyui-output" }] },
    ],
    sources: [
      { id: "artifacts", label: "AI-VIDEO Artifacts", status: "available" },
      { id: "comfyui-output", label: "ComfyUI Output", status: "available" },
      { id: "missing", label: "Missing", status: "unavailable" },
    ],
  };

  assert.deepEqual(externalSourceOptions(catalog), [
    { id: "all", label: "全部外部来源", count: 3, disabled: false },
    { id: "artifacts", label: "AI-VIDEO Artifacts", count: 2, disabled: false },
    { id: "comfyui-output", label: "ComfyUI Output", count: 2, disabled: false },
    { id: "missing", label: "Missing", count: 0, disabled: true },
  ]);
});

test("audible media contract detects tracks and explicitly enables playback", async () => {
  const stopped = [];
  const videoWithAudio = {
    captureStream: () => ({
      getAudioTracks: () => [{ stop: () => stopped.push("audio") }],
      getVideoTracks: () => [{ stop: () => stopped.push("video") }],
    }),
  };
  assert.equal(mediaHasAudioTrack(videoWithAudio), true);
  assert.deepEqual(stopped, ["audio", "video"]);
  assert.equal(mediaHasAudioTrack({ captureStream: () => ({ getAudioTracks: () => [], getVideoTracks: () => [] }) }), false);
  assert.equal(mediaHasAudioTrack({}), null);

  let played = false;
  const playable = {
    defaultMuted: true,
    muted: true,
    volume: 0,
    ended: true,
    currentTime: 5,
    play: async () => { played = true; },
  };
  await enableMediaSound(playable);
  assert.equal(playable.defaultMuted, false);
  assert.equal(playable.muted, false);
  assert.equal(playable.volume, 1);
  assert.equal(playable.currentTime, 0);
  assert.equal(played, true);
});

test("external catalog response maps static non-JSON failures to a stable Chinese unavailable state", async () => {
  const catalog = { groups: [], sources: [] };
  assert.deepEqual(await readExternalCatalogResponse({ ok: true, json: async () => catalog }), catalog);
  await assert.rejects(
    readExternalCatalogResponse({ ok: false, json: async () => { throw new SyntaxError("Unexpected token"); } }),
    /外部媒体数据源不可用/,
  );
});

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

test("catalog change feed batches recursive source events and closes every watcher", async () => {
  const callbacks = new Map();
  const closed = [];
  const watchFactory = (root, options, callback) => {
    assert.deepEqual(options, { recursive: true });
    callbacks.set(root, callback);
    return {
      on() { return this; },
      close() { closed.push(root); },
    };
  };
  const feed = createCatalogChangeFeed({
    roots: [{ id: "runs", root: "/runs" }, { id: "artifacts", root: "/artifacts" }],
    watchFactory,
    debounceMs: 1,
  });
  const events = [];
  const unsubscribe = feed.subscribe((event) => events.push(event));

  callbacks.get("/runs")("change", "manifest.json");
  callbacks.get("/artifacts")("rename", "shot.mp4");
  await new Promise((resolve) => setTimeout(resolve, 10));

  assert.equal(events.length, 1);
  assert.deepEqual(events[0].sources, ["artifacts", "runs"]);
  assert.equal(events[0].sequence, 1);
  unsubscribe();
  feed.close();
  assert.deepEqual(closed.sort(), ["/artifacts", "/runs"]);
});

test("catalog change feed exposes unavailable watchers and runtime failures", () => {
  const runtimeWatcher = new EventEmitter();
  runtimeWatcher.close = () => {};
  const feed = createCatalogChangeFeed({
    roots: [{ id: "runs", root: "/runs" }, { id: "artifacts", root: "/artifacts" }],
    watchFactory(root) {
      if (root === "/artifacts") throw new Error("unwatchable");
      return runtimeWatcher;
    },
  });
  const events = [];
  feed.subscribe((event) => events.push(event));

  assert.deepEqual(feed.status(), {
    expected_sources: ["artifacts", "runs"],
    sources: ["runs"],
    unavailable_sources: ["artifacts"],
  });
  runtimeWatcher.emit("error", new Error("watch failed"));
  assert.deepEqual(feed.status(), {
    expected_sources: ["artifacts", "runs"],
    sources: [],
    unavailable_sources: ["artifacts", "runs"],
  });
  assert.equal(events.at(-1).kind, "source-status");
  feed.close();
});

test("library events endpoint streams local catalog changes and releases its subscription", async () => {
  let listener;
  let unsubscribed = false;
  const changeFeed = {
    status: () => ({
      expected_sources: ["artifacts", "runs"],
      sources: ["artifacts", "runs"],
      unavailable_sources: [],
    }),
    subscribe(callback) {
      listener = callback;
      return () => { unsubscribed = true; };
    },
  };
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-events-"));
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    changeFeed,
  });
  const req = Object.assign(new EventEmitter(), request("GET", "/api/library-events"));
  const streamed = await invoke(handler, req);

  assert.equal(streamed.res.statusCode, 200);
  assert.equal(streamed.res.headers.get("content-type"), "text/event-stream; charset=utf-8");
  assert.match(streamed.res.body.toString(), /event: ready/);
  assert.match(streamed.res.body.toString(), /"expected_sources":\["artifacts","runs"\]/);

  listener({ sources: ["runs"], sequence: 7, observed_at: "2026-08-28T08:00:00.000Z" });
  assert.match(streamed.res.body.toString(), /event: catalog-change/);
  assert.match(streamed.res.body.toString(), /"sequence":7/);
  listener({ kind: "source-status", expected_sources: ["artifacts", "runs"], sources: ["runs"], unavailable_sources: ["artifacts"] });
  assert.match(streamed.res.body.toString(), /event: source-status/);
  assert.match(streamed.res.body.toString(), /"unavailable_sources":\["artifacts"\]/);
  req.emit("close");
  assert.equal(unsubscribed, true);

  const method = await invoke(handler, request("POST", "/api/library-events"));
  assert.equal(method.res.statusCode, 405);
  assert.equal(method.res.headers.get("allow"), "GET");
});

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

test("external media catalog is parallel to runs, source-qualified, and never leaks allowlist roots", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-api-"));
  const sourceRoot = path.join(root, "artifacts");
  const media = path.join(sourceRoot, "qingyan", "shot-01.mp4");
  const bytes = Buffer.from("external-video-bytes");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  const reference = path.join(sourceRoot, "qingyan", "reference.png");
  const referenceBytes = Buffer.from("exact-reference-image-bytes");
  const referenceSha256 = createHash("sha256").update(referenceBytes).digest("hex");
  await mkdir(path.dirname(media), { recursive: true });
  await Promise.all([writeFile(media, bytes), writeFile(reference, referenceBytes)]);
  const calls = [];
  const projection = {
    status: "ok",
    boundary: { read_only: true, canonical: false },
    sources: [{ id: "artifacts", label: "AI-VIDEO Artifacts", kind: "development_artifact", status: "available" }],
    groups: [{
      sha256,
      status: "NOT_EVALUATED",
      evidence_level: "non_canonical",
      unsafe_note: `路径：${sourceRoot}`,
      locations: [{ source_id: "artifacts", relative_path: "qingyan/shot-01.mp4", token: "external_artifacts_token" }],
      shot_evidence: [{
        shot_id: "shot-01",
        reference_inputs: [{ token: "external_artifacts_reference", sha256: referenceSha256 }],
      }],
    }],
    _media: {
      external_artifacts_token: {
        source_id: "artifacts",
        source_path: media,
        mime_type: "video/mp4",
        bytes: bytes.length,
        sha256,
      },
      external_artifacts_reference: {
        source_id: "artifacts",
        source_path: reference,
        mime_type: "image/png",
        bytes: referenceBytes.length,
        sha256: referenceSha256,
      },
      external_unknown_token: {
        source_id: "unknown",
        source_path: media,
        mime_type: "video/mp4",
        bytes: bytes.length,
        sha256,
      },
    },
  };
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    externalSources: [{ id: "artifacts", label: "AI-VIDEO Artifacts", kind: "development_artifact", root: sourceRoot }],
    externalCatalog: async (options) => { calls.push(options); return projection; },
  });

  const catalog = await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(catalog.res.statusCode, 200);
  assert.equal(catalog.res.headers.get("cache-control"), "no-store");
  assert.equal(catalog.res.body.toString().includes(sourceRoot), false);
  assert.equal(catalog.res.body.toString().includes("source_path"), false);
  assert.equal(JSON.parse(catalog.res.body).groups[0].status, "NOT_EVALUATED");
  assert.equal(JSON.parse(catalog.res.body).groups[0].unsafe_note, null);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].sources[0].root, sourceRoot);

  const ranged = await invoke(handler, request("GET", "/api/external-media/media/external_artifacts_token", { range: "bytes=0-7" }));
  assert.equal(ranged.res.statusCode, 206);
  assert.deepEqual(ranged.res.body, bytes.subarray(0, 8));
  assert.equal(ranged.res.headers.get("content-type"), "video/mp4");

  const head = await invoke(handler, request("HEAD", "/api/external-media/media/external_artifacts_token"));
  assert.equal(head.res.statusCode, 200);
  assert.equal(head.res.body.length, 0);

  const referenceResponse = await invoke(handler, request("GET", "/api/external-media/media/external_artifacts_reference"));
  assert.equal(referenceResponse.res.statusCode, 200);
  assert.deepEqual(referenceResponse.res.body, referenceBytes);
  assert.equal(referenceResponse.res.headers.get("content-type"), "image/png");

  const unknownSource = await invoke(handler, request("GET", "/api/external-media/media/external_unknown_token"));
  assert.equal(unknownSource.res.statusCode, 404);
  const method = await invoke(handler, request("POST", "/api/external-media"));
  assert.equal(method.res.statusCode, 405);
  assert.equal(method.res.headers.get("allow"), "GET");
});

test("external media catalog caches repeated reads and invalidates on explicit refresh or source changes", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-cache-"));
  const sourceRoot = path.join(root, "artifacts");
  await mkdir(sourceRoot);
  let onCatalogChange = null;
  let catalogCalls = 0;
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    externalSources: [{ id: "artifacts", label: "Artifacts", kind: "development_artifact", root: sourceRoot }],
    externalCatalog: async () => ({
      boundary: { read_only: true },
      sources: [],
      groups: [{ sha256: String(catalogCalls += 1).padStart(64, "0") }],
      _media: {},
    }),
    changeFeed: {
      subscribe(callback) { onCatalogChange = callback; return () => { onCatalogChange = null; }; },
    },
  });

  const first = await invoke(handler, request("GET", "/api/external-media"));
  const cached = await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(catalogCalls, 1);
  assert.deepEqual(JSON.parse(cached.res.body), JSON.parse(first.res.body));

  onCatalogChange({ sources: ["runs"] });
  await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(catalogCalls, 1);

  const forced = await invoke(handler, request("GET", "/api/external-media?refresh=1"));
  assert.equal(catalogCalls, 2);
  assert.equal(JSON.parse(forced.res.body).groups[0].sha256, "2".padStart(64, "0"));

  onCatalogChange({ sources: ["artifacts"] });
  const changed = await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(catalogCalls, 3);
  assert.equal(JSON.parse(changed.res.body).groups[0].sha256, "3".padStart(64, "0"));
  handler.close();
});

test("external media cache discards an in-flight scan invalidated by a source change", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-cache-serial-"));
  const sourceRoot = path.join(root, "artifacts");
  await mkdir(sourceRoot);
  let onCatalogChange = null;
  let catalogCalls = 0;
  let releaseFirst;
  const firstProjection = new Promise((resolve) => { releaseFirst = resolve; });
  const projection = (label) => ({
    boundary: { read_only: true },
    sources: [],
    groups: [{ sha256: label.repeat(64) }],
    _media: {},
  });
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    externalSources: [{ id: "artifacts", label: "Artifacts", kind: "development_artifact", root: sourceRoot }],
    externalCatalog: async () => {
      catalogCalls += 1;
      return catalogCalls === 1 ? firstProjection : projection("b");
    },
    changeFeed: {
      subscribe(callback) { onCatalogChange = callback; return () => { onCatalogChange = null; }; },
    },
  });

  const first = invoke(handler, request("GET", "/api/external-media"));
  onCatalogChange({ sources: ["artifacts"] });
  const concurrent = invoke(handler, request("GET", "/api/external-media"));
  releaseFirst(projection("a"));
  const [firstResponse, concurrentResponse] = await Promise.all([first, concurrent]);

  assert.equal(catalogCalls, 2);
  assert.equal(JSON.parse(firstResponse.res.body).groups[0].sha256, "b".repeat(64));
  assert.equal(JSON.parse(concurrentResponse.res.body).groups[0].sha256, "b".repeat(64));
  await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(catalogCalls, 2);
  handler.close();
});

test("external media cache shares an in-flight scan failure without retry amplification", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-cache-failure-"));
  const sourceRoot = path.join(root, "artifacts");
  await mkdir(sourceRoot);
  let catalogCalls = 0;
  let rejectFirst;
  const firstProjection = new Promise((resolve, reject) => { rejectFirst = reject; });
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    externalSources: [{ id: "artifacts", label: "Artifacts", kind: "development_artifact", root: sourceRoot }],
    externalCatalog: async () => {
      catalogCalls += 1;
      if (catalogCalls === 1) return firstProjection;
      return { boundary: { read_only: true }, sources: [], groups: [], _media: {} };
    },
  });

  const requests = [
    invoke(handler, request("GET", "/api/external-media")),
    invoke(handler, request("GET", "/api/external-media")),
    invoke(handler, request("GET", "/api/external-media")),
  ];
  rejectFirst(new Error("source unavailable"));
  const failed = await Promise.all(requests);

  assert.equal(catalogCalls, 1);
  assert.deepEqual(failed.map(({ res }) => res.statusCode), [503, 503, 503]);
  const retried = await invoke(handler, request("GET", "/api/external-media"));
  assert.equal(retried.res.statusCode, 200);
  assert.equal(catalogCalls, 2);
});

test("Runs media context index is read-only, GET-only, and sanitized", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-runs-media-index-"));
  const secretRoot = path.join(root, "private");
  let projectorCalls = 0;
  let onCatalogChange = null;
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    runsMediaIndexProjector: async () => { projectorCalls += 1; return ({
      boundary: { read_only: true, association: "exact_sha256_and_bytes", lifecycle_projection: false, complete: true },
      bindings: [{
        sha256: "a".repeat(64),
        bytes: 123,
        workspace: "run-a/project.yaml",
        attempt_id: "attempt-a",
        prompt_text: "Exact prompt.",
        unsafe_path: secretRoot,
      }],
    }); },
    changeFeed: {
      subscribe(callback) { onCatalogChange = callback; return () => { onCatalogChange = null; }; },
    },
  });

  const response = await invoke(handler, request("GET", "/api/runs/media-context-index"));
  assert.equal(response.res.statusCode, 200);
  const body = JSON.parse(response.res.body);
  assert.equal(body.boundary.association, "exact_sha256_and_bytes");
  assert.equal(body.bindings[0].workspace, "run-a/project.yaml");
  assert.equal(body.bindings[0].unsafe_path, null);
  assert.equal(response.res.body.toString().includes(secretRoot), false);
  const cached = await invoke(handler, request("GET", "/api/runs/media-context-index"));
  assert.equal(cached.res.statusCode, 200);
  assert.equal(projectorCalls, 1);
  onCatalogChange({ sources: ["runs"] });
  const refreshed = await invoke(handler, request("GET", "/api/runs/media-context-index"));
  assert.equal(refreshed.res.statusCode, 200);
  assert.equal(projectorCalls, 2);

  const method = await invoke(handler, request("POST", "/api/runs/media-context-index"));
  assert.equal(method.res.statusCode, 405);
  assert.equal(method.res.headers.get("allow"), "GET");
});

test("Runs media context invalidation serializes an in-flight full index rebuild", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-runs-media-serial-"));
  let onCatalogChange = null;
  let projectorCalls = 0;
  let releaseFirst;
  const firstProjection = new Promise((resolve) => { releaseFirst = resolve; });
  const staleIndex = {
    boundary: { read_only: true, association: "exact_sha256_and_bytes", lifecycle_projection: false, complete: true },
    bindings: [{ sha256: "a".repeat(64), bytes: 1, attempt_id: "stale" }],
  };
  const completeIndex = {
    ...staleIndex,
    bindings: [{ sha256: "a".repeat(64), bytes: 1, attempt_id: "fresh" }],
  };
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    runsMediaIndexProjector: async () => {
      projectorCalls += 1;
      return projectorCalls === 1 ? firstProjection : completeIndex;
    },
    changeFeed: {
      subscribe(callback) { onCatalogChange = callback; return () => { onCatalogChange = null; }; },
    },
  });

  const first = invoke(handler, request("GET", "/api/runs/media-context-index"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(projectorCalls, 1);
  onCatalogChange({ sources: ["runs"] });
  const second = invoke(handler, request("GET", "/api/runs/media-context-index"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(projectorCalls, 1);

  releaseFirst(staleIndex);
  const [refreshedFirst, refreshedSecond] = await Promise.all([first, second]);
  assert.equal(refreshedFirst.res.statusCode, 200);
  assert.equal(refreshedSecond.res.statusCode, 200);
  assert.equal(JSON.parse(refreshedFirst.res.body).bindings[0].attempt_id, "fresh");
  assert.equal(JSON.parse(refreshedSecond.res.body).bindings[0].attempt_id, "fresh");
  assert.equal(projectorCalls, 2);
});

test("external media serving revalidates containment and exact bytes", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-external-swap-"));
  const sourceRoot = path.join(root, "comfy-output");
  const media = path.join(sourceRoot, "clip.mp4");
  const outside = path.join(root, "outside.mp4");
  const bytes = Buffer.from("0123456789");
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  await mkdir(sourceRoot, { recursive: true });
  await writeFile(media, bytes);
  await writeFile(outside, bytes);
  const descriptor = {
    source_id: "comfyui-output",
    source_path: media,
    mime_type: "video/mp4",
    bytes: bytes.length,
    sha256,
  };
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({ workspaces: [] }),
    externalSources: [{ id: "comfyui-output", label: "ComfyUI Output", kind: "raw_provider_output", root: sourceRoot }],
    externalCatalog: async () => ({ status: "ok", sources: [], groups: [], _media: { external_comfy_token: descriptor } }),
  });
  await invoke(handler, request("GET", "/api/external-media"));

  await unlink(media);
  await symlink(outside, media);
  const escaped = await invoke(handler, request("GET", "/api/external-media/media/external_comfy_token"));
  assert.equal(escaped.res.statusCode, 503);
  assert.equal(escaped.res.body.toString().includes(outside), false);

  await unlink(media);
  await writeFile(media, "abcdefghij");
  const replaced = await invoke(handler, request("GET", "/api/external-media/media/external_comfy_token"));
  assert.equal(replaced.res.statusCode, 503);
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

test("media endpoint serves an HTML wrapper when client accepts text/html", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-html-"));
  const image = path.join(root, "runs", "demo", "still.png");
  await mkdir(path.dirname(image), { recursive: true });
  const imageBytes = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  await writeFile(image, imageBytes);
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      workspace: "demo/project.yaml",
      attempts: [],
      _media: { stilltoken: { source_path: image, mime_type: "image/png", bytes: imageBytes.length } },
    }),
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));

  const html = await invoke(handler, request("GET", "/api/runs/media/stilltoken", { accept: "text/html,application/xhtml+xml" }));
  assert.equal(html.res.statusCode, 200);
  assert.equal(html.res.headers.get("content-type"), "text/html; charset=utf-8");
  const body = html.res.body.toString("utf8");
  assert.equal(body.includes("<!doctype html>"), true);
  assert.equal(body.includes("返回 Console"), true);
  assert.equal(body.includes('href="/"'), true);
  assert.equal(body.includes('<img class="frame" src="/api/runs/media/stilltoken" alt="已注册图片" />'), true);
  assert.equal(body.includes("image/png"), true);
  assert.equal(body.includes(`${imageBytes.length.toLocaleString("en-US")} bytes`), true);
  assert.equal(body.includes(image), false);
});

test("video HTML wrapper explicitly enables sound inside the user gesture", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-video-html-"));
  const video = path.join(root, "runs", "demo", "clip.mp4");
  const bytes = Buffer.from("0123456789");
  await mkdir(path.dirname(video), { recursive: true });
  await writeFile(video, bytes);
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      workspace: "demo/project.yaml",
      attempts: [],
      _media: { videotoken: { source_path: video, mime_type: "video/mp4", bytes: bytes.length } },
    }),
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));

  const html = await invoke(handler, request("GET", "/api/runs/media/videotoken", { accept: "text/html" }));
  assert.equal(html.res.statusCode, 200);
  const body = html.res.body.toString("utf8");
  assert.match(body, /<video id="registered-video"[^>]*controls[^>]*playsinline/);
  assert.match(body, /<link rel="icon" href="data:," \/>/);
  assert.match(body, /开启声音并播放/);
  assert.match(body, /video\.defaultMuted = false;/);
  assert.match(body, /video\.muted = false;/);
  assert.match(body, /video\.volume = 1;/);
  assert.match(body, /if \(video\.ended\) video\.currentTime = 0;/);
  assert.match(body, /soundButton\.addEventListener\("click", async \(\) =>/);
  assert.match(body, /await video\.play\(\);/);
  assert.equal(body.includes(video), false);
});

test("media endpoint keeps serving bytes when client omits Accept", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-bytes-"));
  const media = path.join(root, "runs", "demo", "clip.mp4");
  await mkdir(path.dirname(media), { recursive: true });
  const bytes = Buffer.from("0123456789");
  await writeFile(media, bytes);
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      workspace: "demo/project.yaml",
      attempts: [],
      _media: { bytetoken: { source_path: media, mime_type: "video/mp4", bytes: bytes.length } },
    }),
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));

  const plain = await invoke(handler, request("GET", "/api/runs/media/bytetoken"));
  assert.equal(plain.res.statusCode, 200);
  assert.equal(plain.res.headers.get("content-type"), "video/mp4");
  assert.equal(plain.res.body.equals(bytes), true);

  const ranged = await invoke(handler, request("GET", "/api/runs/media/bytetoken", { range: "bytes=0-3" }));
  assert.equal(ranged.res.statusCode, 206);
  assert.equal(ranged.res.headers.get("content-type"), "video/mp4");
  assert.equal(ranged.res.body.equals(bytes.subarray(0, 4)), true);
});

test("HEAD on media endpoint skips HTML wrapper and returns media headers", async () => {
  const root = await mkdtemp(path.join(tmpdir(), "provider-console-head-"));
  const media = path.join(root, "runs", "demo", "video.mp4");
  await mkdir(path.dirname(media), { recursive: true });
  await writeFile(media, "0123456789");
  const handler = createRunsApiHandler({
    repoRoot: root,
    runProjector: async () => ({
      workspace: "demo/project.yaml",
      attempts: [],
      _media: { headtoken: { source_path: media, mime_type: "video/mp4", bytes: 10 } },
    }),
  });
  await invoke(handler, request("GET", "/api/runs/detail?workspace=demo%2Fproject.yaml"));

  const head = await invoke(handler, request("HEAD", "/api/runs/media/headtoken", { accept: "text/html" }));
  assert.equal(head.res.statusCode, 200);
  assert.equal(head.res.headers.get("content-type"), "video/mp4");
  assert.equal(head.res.headers.get("content-length"), 10);
  assert.equal(head.res.body.length, 0);
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

  const events = await invoke(handler, { ...request("GET", "/api/library-events"), socket: { remoteAddress: "192.168.1.50" } });
  assert.equal(events.res.statusCode, 403);
  assert.equal(called, false);

  const missingAddress = await invoke(handler, { ...request("GET", "/api/runs"), socket: {} });
  assert.equal(missingAddress.res.statusCode, 403);
  assert.equal(called, false);
});
