---
record_kind: architecture_implementation
topic_id: provider-console-composed-run-outputs
learning_eligibility: ineligible
---

# Provider Console Composed Run Outputs Record

Date: 2026-08-30

## Purpose

本文记录 Provider Console 无法看到 `runs/<run_id>/outputs/**` 新合成视频的 deterministic integration gap、
实现边界和真实浏览器验证。它是 local read-only catalog 修复，不是媒体生成、Production state、candidate、
P6、Final Acceptance、publish 或 release evidence。

## Runtime Truth And Fix

问题不是 `make frontend` 缺少 HMR，而是默认 External source allowlist 没有 `runs` composition outputs。
Commit `3b8faf32b06a0dc500ba462c1eebe7e34e73497c` 完成以下修复：

- 新增 `runs-outputs` source，root 为 repository `runs/`，layout 为 `run_outputs`；
- scanner 只读取 direct `runs/<run_id>/outputs/**` media 与同 workspace `sidecars/**`，排除
  `<run_id>/production/**/state/render/outputs/**`；
- sidecar limit 按 media 所属 top-level run 隔离，避免全 `runs/` JSON 排序截断后漏掉较新的 composition gate；
- 只支持 `development-composition-repair-gate-1.0` 与
  `development-composition-human-verdict-1.0` 的窄 adapter；human verdict 必须同时绑定 exact MP4 path/SHA、
  prior technical gate path/SHA，且两层均声明 `production_or_final_acceptance=false`；
- 同一 exact SHA 有多个副本时，完整 human chain 优先于 technical-only copy；非空 `technical_gate` 或
  `human_verdict` 冲突 fail closed；human enum 只接受 `PASS`、`FAIL`、`NOT_EVALUATED`。

所有输出继续标记 `evidence_classification=non_canonical`。该 source 不创建第二套 Manifest、timeline、candidate、
activation 或 quality-acceptance owner。

## Exact Artifact And Live Evidence

本轮目标文件：

`runs/drama-h3-t8-30s-preview-20260830-final-v2/outputs/key-at-the-waiting-room-development-preview-v2-30.000s.mp4`

- bytes: `10839150`
- SHA-256: `c4ca36017f48a398eb15765b8342e4f198a3c7e79fa06de13a2450e9b56ef5a0`
- generation type projection: `deterministic_composition`
- technical gate: `PASS_FOR_HUMAN_REVIEW`
- exact chained human verdict: `FAIL`
- Production / Final Acceptance: `false`

Live `/api/external-media?refresh=1` 返回 `runs-outputs` available、`media_count=24`，目标 group 的
`metadata_status=bound`、`reported_status=FAIL`。Chrome 中来源下拉出现 `AI-VIDEO Runs Outputs`，目标卡片
显示 `FAIL`；播放器使用 opaque `/api/external-media/media/...` token，`readyState=4`、`duration=30`，media
request 返回 HTTP `206`，console 无 error/warn。

该 playback evidence 只证明 exact file 可见和可播放。Human `FAIL` 仍是当前质量 verdict，不能由 technical
gate、播放器 ready 或 build/test PASS 覆盖。

## Verification

- Provider Console Node suite：`90 passed`。
- `npm run build`：PASS，`4582 modules transformed`。
- independent `reviewer_xhigh` 初审发现 duplicate-SHA evidence completeness 与未知 verdict enum 两个问题；修复后
  scoped re-review：`accept`，无 blocking/non-blocking concern。
- Harness exact commit range `ff7e393..3b8faf3` 的 10 个 mandatory checks 全部 individually passed：
  docs contract、policy audit、skill boundary、Architecture Gate、Provider Console Python `42 passed`、Node
  `85 passed`、web/sites builds 与 sites tests。

Receipt `.agent/harness/runs/20260830T002353506023Z/receipt.json` 的 overall status 是 `failed`，唯一
`failure_reason=source scope changed during verification`：运行期间另一个 concurrent session 把 repository
`HEAD` 从 `3b8faf3` 推进到 unrelated commit `a604c8d`。因此本记录不把该 receipt 宣称为 passing completion
receipt；重新对非-current `3b8faf3` 请求 completion verification 会按 Harness contract 返回
`completion scope is not closure eligible`。

## Boundaries And Remaining Risk

- `runs-outputs` 是 External/non-canonical catalog，不改变 canonical Runs latest-follow。
- 文件名、mtime 或目录位置不会生成 Prompt、Shot、success、candidate 或 lifecycle truth；只有窄 schema 的 exact
  evidence chain可投影 composition review status。
- 未调用 Provider、未生成媒体、未修改 Manifest 或 activation state。
- `retrieve-ai-video-memory` exact CLI 因当前 Python 环境缺少 `langchain_core` 返回
  `ModuleNotFoundError`；没有重建 index，也没有用 text search 冒充 RAG。
- Automatic `distill-ai-video-learning` evaluation outcome：`no_candidate`。本轮只有一条 deterministic
  integration failure/fix chain，不满足跨实验 Learning Claim admission threshold，也不创建 placeholder。
- Implementation 与 record 均为 local commits；未 push、deploy 或 release。

## Agent Guardrails

- 不得把 `runs-outputs` 卡片当成 Production attempt 或 delivery truth。
- 不得把 technical `PASS_FOR_HUMAN_REVIEW` 覆盖 human `FAIL`。
- 不得扩大 layout 到 arbitrary recursive `runs/` scan；nested Production render 必须继续排除。
- 不得对 unknown composition schema 或未知 verdict 字符串做 best-effort 解释。
