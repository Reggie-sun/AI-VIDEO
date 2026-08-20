# Video Planner And Quality Gate Handoff Record

Date: 2026-08-21

## Purpose

本文记录 provider-neutral Video Planner implementation 的稳定 checkpoint、其
Harness blocker closure，以及后续 Shot Quality Gate spec v3 与 Local H3 C2
quality iteration 的真实边界。

本记录不是新的 Provider execution authorization，也不把尚未修订的
`docs/specs/shot-quality-gate/` v2 draft、尚未生成的 Local H3 candidate 或未来
人工 GO/NO-GO 描述成 runtime truth。

## Current Runtime Truth

Video Planner 已在 local `main` 的两个 task commits 中实现并完成 gate closure：

- `779d40d feat: add provider-neutral video planner preflight`
- `a232d15 fix: close video planner harness gates`

`779d40d` 新增 `src/ai_video/planning/` public surface、immutable planner models、
provider-neutral `VideoPlanner`、fixtures 与 focused tests。当前 contract 包括：

- models frozen 且 `extra="forbid"`；
- `ShotIntentEvidence`、`ReviewDecisionProjection` 与 `AvailableAsset` 只投影既有
  AI-VIDEO truth；
- `AssetRole.APPROVED_REUSABLE_PLATE` 与
  `ProductionPolicyInput.accept_static_image_fallback`；
- sealed `VideoPlanningRequest.create()` 与 `VideoGenerationPlan.create()`；
- `source_request_content_hash` 精确绑定 current request；
- diagnostic `request_id` 不改变 semantic request hash；
- deterministic `plan_id`；
- `PlanOutcome` 仅有 `PROPOSED` 与 `BLOCKED`；
- stale plan、BLOCKED plan、missing current request hash 与 Main Agent STOP seam
  均 fail closed。

Planner 只提出 plan，不选择或调用 Provider，不写 Production Shot、Asset Registry、
Manifest、Dependency Graph、Review 或 delivery state。External creative Skills 仍只提供
authoring advice，不进入 runtime。

`a232d15` 关闭了 Planner implementation 暴露出的 repository gates：

- `.agent/harness/policy.yaml` 为 planning paths 增加 exact routing；
- HyperFrames HTML/CSS source serialization 被提取到
  `src/ai_video/production/_hyperframes_source.py`，消除本次 oversized-module
  growth error；
- caption `max_width_milli=900` 正确序列化为 `width:90%`；
- voice/captions E2E fake runner 以 class token 匹配
  `clip caption caption-style-*`，不再依赖 exact class string。

以上 HyperFrames 修复没有新增 timeline、renderer、writer 或 lifecycle owner。

## Verification And Receipt State

Planner focused suite 的 durable closure evidence 位于：

```text
.agent/harness/runs/video-planner-complete-20aeeff-a232d15/
```

该 receipt 在 `a232d15` checkpoint 执行并通过：

- `harness_tests`: `53 passed`
- `cli_config_tests`: `13 passed`
- `production_composition_audio_tests`: `924 passed, 3 skipped`
- `video_planner_tests`: `101 passed`
- Architecture Gate: `PASS (0 errors, 0 warnings, 0 info)`

该 combined range 从 `20aeeff` 到 `a232d15`，除 Planner 与 gate fix 外还包含
intervening control-plane changes。因此它是 closure-range evidence，不是
`779d40d` 的 task-only ownership proof。

Gate-fix task-only receipt 位于：

```text
.agent/harness/runs/video-planner-gates-commit-a232d15/receipt.json
```

其 exact range 为 `779d40d..a232d15`，通过 `53` 个 Harness tests、
`924 passed, 3 skipped` composition/audio tests 与 Architecture Gate。

最初的 Planner task-only receipt：

```text
.agent/harness/runs/video-planner-t1-t14-commit-779d40d/receipt.json
```

状态为 `failed`，原因是当时 repository-level full suite 暴露 policy mapping、
HyperFrames architecture 与 caption E2E blockers。不要把该 receipt 单独宣传为
passing acceptance；这些 blockers 由后续 `a232d15` 和上述 passing receipts 关闭。

在 `a232d15` checkpoint，两份 passing receipts 曾在 clean local clone 中验证为
`fresh=true`、`passed=true`、`integrity=true`、`artifact_integrity=true`、
`policy_matches=true` 与 `snapshot_matches=true`。当前 `main` 已前进到
`285757a feat: add scoped multilingual agent memory retrieval`。因此在当前 checkout
重新执行 `verify-receipt` 会得到 `fresh=false`、`snapshot_matches=false`；artifact、
policy 与 receipt integrity 仍通过。历史 receipt 不能冒充 current-HEAD closure，
后续 change 必须生成自己的 exact staged 或 commit-range receipt。

当前 publication truth：local `main` 相对 `origin/main` 为 `ahead 29`；本记录没有
重新验证 remote publication、GitHub workflow 或 release，因此不得声称已 push 或
released。

## Shot Quality Gate v2 Assessment

`docs/specs/shot-quality-gate/` 当前仍是 draft v2，implementation 未开始。该 draft
不能直接进入 runtime implementation，已确认的主要 contract defects 包括：

1. `VideoQualityGateRequest` 要求 `FetchedVideoCandidate`，但 gate import blacklist
   又禁止其 owner `ai_video.production.video_generation`。
2. spec 使用不存在的 `ProductionStateCommitter.commit_video_activation`；当前实际
   activation API 是 `activate_video_candidate`。
3. `VideoFetchReceipt` 与 `LocalVideoFetchReceipt` 已在 typed model validation 中
   验证 `fetch_fingerprint`；remote fetch construction 也已验证 expected content
   type。v2 post-fetch checks 与 existing owner 重复，且缺少独立解析 linked
   `VideoSubmission.expected_content_type` 的 typed input seam。
4. spec 同时把 receipts 描述为 disposable side evidence，又要求把 receipt hash
   写入 `VideoGenerationAttemptState`；这必须被明确为独立 schema/lifecycle migration，
   或从首个 advisory gate slice 移除。
5. `intent.split()` 不是可靠的 multilingual complexity contract；README 的 T1-T12、
   tasks 的 T1-T18、缺失的 D1-D5 anchors 与已有 `integration.md` 状态也不一致。

后续 spec v3 必须先做 owner audit。默认方向是优先收敛纯 deterministic、no-I/O、
pre-submit `ShotReadinessGate`，消费 accepted `VideoGenerationPlan` 而不重算 Planner
truth；对重复的 post-fetch gate 与 committer/Manifest seam，应删除、延期或通过新的
provider-neutral projection 和独立 migration contract 重新设计。

为并行隔离已创建：

```text
branch: agent/shot-quality-gate-spec-v3
worktree: /home/reggie/vscode_folder/AI-VIDEO-shot-quality-gate-spec-v3
base: a232d15
```

该 branch/worktree 的存在不证明 v3 已修订、reviewed、committed 或 merged。

## Media Quality Next Work

Shot Quality Gate v2 明确不评估 identity drift、动作自然度、composition、camera、
hard-cut seam 或 subjective continuity quality。因此实现 structural gate 不能替代
真实视频生成与人工观看。

Local H3 C2 的正确下一 lane 是 bounded controlled generation：使用现有
loopback-only `minimax_h3_fl2va_quality_local` profile，重新核实 active
Project/Manifest/Registry、terminal 与 derived keyframe lineage，每轮只改变一个
creative variable，最多生成三个 candidates，并在每轮执行 `ffprobe`、project-local
`video-analysis`、frame/contact-sheet comparison 与人工 GO/NO-GO。

技术 lineage、hash、SSIM、fetch success 或 analyzer PASS 均不等于 subjective quality
acceptance。没有用户明确 GO 前，不得称 C2 quality accepted，也不得批量扩量。

本记录过程没有调用 Local H3、ComfyUI、Hailuo、Seedance 或任何 remote/paid Provider，
没有生成或修改媒体，也没有读取 credential。

## Agent Guardrails

后续 Agent 必须保持以下区分：

- `VideoGenerationPlan.PROPOSED` 不等于 Provider authorization、generation success
  或 quality acceptance。
- Planner/Quality Gate receipt 不等于 Production Manifest、Review evidence 或 final
  delivery truth。
- structural preflight PASS 不等于画面可看。
- previous receipt passed at `a232d15` 不等于 current `main` receipt fresh。
- quality-gate v2 docs 不等于 approved v3 contract 或 implemented runtime。
- Local H3 candidate technical PASS 不等于用户 GO。

Spec v3 writer 与 media-generation writer 必须保持独立 branch/worktree ownership。
任何新 Provider call、schema migration、committer seam、Manifest field 或 quality claim
仍需遵守当前 `AGENTS.md`、canonical contracts 与 exact verification gates。
