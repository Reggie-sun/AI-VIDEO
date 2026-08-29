---
record_kind: architecture_implementation
topic_id: provider-console-latest-video-follow
learning_eligibility: ineligible
---

# Provider Console Latest Video Follow Record

Date: 2026-08-30

## Purpose

本文记录 Provider Console “实时更新已连接，但播放器仍停留在旧视频” regression 的 current root cause、
implementation checkpoint、真实浏览器证据与 remaining boundary。

这是 local read-only Console 的工程修复记录，不是 Provider、媒体生成、candidate activation、P6、
Final Acceptance、publish 或 release evidence。代码、tests、exact Harness receipt 与当前 runtime evidence
仍是 source of truth。

## Root Cause

SSE 通知链本身已连通：`fs.watch -> /api/library-events -> useLibraryLiveUpdates() -> refresh()`。
实际断点位于 refresh 后的 selection policy：

- Runs refresh 优先保留旧 workspace，并在 Manifest append-order attempts 中选择最早项；
- External refresh 只要旧 SHA 仍存在就继续保留；
- 一个 global follow flag 会让 Runs 与 External 的历史 pin 相互污染；
- `/api/runs` 的 `updated_at` 来自 project/Manifest marker mtime，只能表示 workspace 更新，不能证明
  最新 `video_generation` attempt。

因此“实时更新已连接”只证明 watcher/SSE coverage，不证明当前 player 已关联最新视频。

## Implementation And Contracts

Product implementation checkpoint：

- `cb40fe7220999495e033f5092b1dd90778081a8f`：前端新增 `auto-follow-latest` 与 manual pin
  reconciliation；attempts 按 `started_at` newest-first；Runs/External follow state 分离；manual attempt
  selection 推进 workspace selection epoch，使 in-flight refresh 无法覆盖历史 pin。
- catalog 只从 typed `ProductionManifest` 中投影 `latest_video_attempt_at`。普通 workspace mtime、Legacy
  Manifest、invalid Manifest 与 loose MP4 均不能产生该 hint；前端仍对选中的 workspace 执行 strict detail
  reopen，再使用 canonical media token。
- `6ac23978f9fb169473d5193e174acf7810c84168`：将 bounded/no-follow Manifest reader 与 latest-attempt
  projection 提取到 `src/ai_video/provider_console_manifest.py`；`provider_console.py` 与
  `provider_console_video_evidence.py` 复用同一 reader，消除 oversized-module growth 与双读取路径。
- `9040ce7783bfb803f6003d23d85735ce685f6f68`：把新模块精确路由到既有 `provider_console` Harness
  category，并以 `tests/test_agent_harness.py` 锁定 `fallback_paths=[]` 与 mandatory checks。

保持不变的 contracts：

- Provider Console 仍为 loopback、read-only、local-only observer；
- `ProductionManifest` 与 `ProductionStateCommitter` ownership 未改变；
- media 只通过 strict detail projection / exact registered token 播放；
- refresh 不提交 Provider、不重试、不写 Manifest、不激活 candidate，也不签发任何 quality verdict。

## Verification And Runtime Evidence

Focused current-tree verification：

- `tests/test_provider_console.py`：`36 passed`；final Harness Provider Console Python lane：`42 passed`。
- Provider Console Node suite：`81 passed`。
- `tests/test_agent_harness.py`：targeted `133 passed`；final Harness control-plane lane：`204 passed`。
- `npm --prefix provider-console run build`：PASS，`4582 modules transformed`。
- Architecture Gate：`PASS (0 error(s), 0 warning(s), 0 info finding(s))`。
- independent product re-review：native `reviewer_high` 最终 `accept with concerns`，无 blocking issue；
  concern 仅为没有新增完整 App-level deferred-fetch race harness。
- architecture extraction re-review：同 tier `accept`；Harness route review：native `reviewer_xhigh` `accept`。

Chrome integrated verification 使用 live `http://127.0.0.1:5173/`：

- `/api/library-events` 为 `200`，Runs 与全部 allowlisted external sources 均处于 watched coverage；
- `/api/runs` 当前 typed latest workspace 为
  `drama-h3-t8-30s-preview-20260830-v24/production-project/project.yaml`，
  `latest_video_attempt_at=2026-08-29T19:01:05.815589+00:00`；
- 页面 strict reopen 后选中 `drama-preview-v24-attempt-06`，视频通过 `/api/runs/media/...` 返回 `206`，
  browser `readyState=4`、`duration=5.166667`；console 无 warning/error；
- 先在 External 选择较旧 exact SHA，再切回 Runs，页面立即重新 reconciliation 到上述 v24 attempt，证明
  External pin 不再污染 Runs follow state。

本轮没有生成新媒体，因此以上 live proof 验证的是 current catalog/detail/player selection 与 source switch，
不是一次“新生成落盘后完整 SSE 推进”的 live Provider/ComfyUI experiment。

Exact completion range：
`c584b5c9254060ffaccb8d32b37aaa85e1c8f10f..9040ce7783bfb803f6003d23d85735ce685f6f68`。
Fresh passing receipt：`.agent/harness/runs/20260829T234340198892Z/receipt.json`。Receipt verifier 的
`passed`、`fresh`、`fresh_for_snapshot`、`scope_paths_match`、`scope_worktree_clean`、
`complete_completion_proof`、`integrity` 与 `artifact_integrity` 均为 `true`。

## Evidence And Scope Boundaries

- filesystem 中较新的 `runs/*/outputs/*.mp4` 若没有 canonical `production-project/project.yaml`、typed
  Manifest attempt 与 registered media identity，不会被 Runs auto-follow。它们不是“前端漏扫”，而是尚未进入
  strict Production workspace contract；不得通过 arbitrary recursive MP4 scan 冒充 latest Production video。
- invalid Manifest 不产生 `latest_video_attempt_at`；detail strict reopen 失败时继续 fail closed。
- lifecycle `running`、fetched bytes、player ready、Harness PASS 与 quality acceptance 保持独立。
- RAG preflight 按 `retrieve-ai-video-memory` 要求尝试 exact project CLI，但当前环境缺少
  `langchain_core`，返回 `ModuleNotFoundError`；本轮没有重建 index、安装 dependency 或用 text search 冒充
  project RAG result。

## Assessment

该 regression 已在 current local checkpoint 修复：当操作员仍处于 auto-follow 状态时，Runs 按 typed latest
video attempt 推进，External 按当前 catalog newest-first 推进；操作员显式回看历史时 selection 保持 pin，
旧异步 response 不得抢回焦点。实现没有创建第二 lifecycle owner、renderer、media catalog truth 或 mutation path。

本记录为 `learning_eligibility: ineligible`：它是一项 deterministic frontend/catalog regression fix，只有一条
工程 failure/fix chain，不构成两个 independent empirical attempts、controlled multi-arm comparison 或 existing
Learning Claim 的 material evidence update。

Automatic `distill-ai-video-learning` evaluation outcome：`no_candidate`。不创建 Learning Claim placeholder，
不进入 confirmation/adoption flow。

## Remaining Risks

- async pin race 由 selection guard test、commit-time reconciliation helper、代码路径与 independent review 覆盖，
  但尚无单个 App-level deferred-fetch test 直接组合复现整个时序；这是 non-blocking regression-test gap。
- 本轮没有在生成一条新的 canonical video attempt 后观察真实 watcher event 自动推进 player；若未来需要把该
  empirical lane升级为 acceptance evidence，应使用 bounded local generation 或 controlled fixture event，并绑定
  exact workspace/attempt/media identity。
- 本 checkpoint 仅存在于 local `main` commits；没有 push、deploy 或 release。

## Agent Guardrails

- 不得把 workspace `updated_at`、filename、directory mtime 或 loose MP4 存在解释为 latest generated video truth。
- 不得为“实时”效果绕过 strict Manifest/detail/media-token contracts。
- 用户 manual pin 必须优先于 stale in-flight refresh；Runs 与 External follow state 不得共享。
- playback success 不等于 candidate、P6、Final Acceptance 或 human visual PASS。
