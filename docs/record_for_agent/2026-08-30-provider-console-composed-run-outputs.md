---
record_kind: architecture_implementation
topic_id: provider-console-composed-run-outputs
learning_eligibility: ineligible
---

# Provider Console Composed Run Outputs Record

Date: 2026-08-30

## Discovery Scope Update — 2026-09-05

下方“只读取 output/outputs”的扫描范围属于历史实现。当前新增 run 根目录直属视频的浅层
发现，保持非 canonical、exact bytes 和内部目录隔离；详见
[Video Library follow-up](2026-09-05-video-library-browsing-and-comparison.md#direct-run-root-follow-up--2026-09-05)。
下方历史 gate、人审及 Provider evidence 不变。

## Purpose

本文记录 Provider Console 无法看到 `runs/<run_id>/outputs/**` 或 `runs/<run_id>/output/**` 新合成视频的 deterministic integration gap、
实现边界和真实浏览器验证。它是 local read-only catalog 修复，不是媒体生成、Production state、candidate、
P6、Final Acceptance、publish 或 release evidence。

## Seedance Singular Output Extension — 2026-08-30

Commit `8c3e33c813ab743aee82067b5f0500a2f443d5cf` 将同一 catalog contract 扩展到 Seedance skyship run：

- `run_outputs` 同时扫描 direct top-level `output/**` 与 `outputs/**`，仍不递归暴露
  `<run_id>/production/**/outputs/**`；
- exact evidence 只从同一 top-level run 的 `sidecars/**` 与 `evidence/**` 读取；
- `REVIEW_V3_CAPTION_AUDIO_CONTRACT` adapter 要求 workspace-relative path、SHA-256、bytes 完全匹配，且
  `publication.candidate_activation`、`publication.p6`、`publication.final_acceptance` 均为 `false`；
- `FINAL_ACCEPTANCE` 作为 exact-bound external reported status；只有 explicit
  `human_playback_finding.verdict` 与其一致时才投影 `human_verdict`；
- 切换视频来源时清除旧的 `externalQuery`，因此截图中遗留的 `rama-h3...` 不会继续隐藏 Seedance 条目。

错误 path、SHA、bytes、publication 标志、含 `.` / `..` 的 path 或冲突 gate 均 fail closed。该扩展仍只产生
`non_canonical` External evidence，不改变 Manifest、candidate、P6、Final Acceptance 或 activation ownership。

## Runtime Truth And Fix

问题不是 `make frontend` 缺少 HMR，而是默认 External source allowlist 没有 `runs` composition outputs。
Commit `3b8faf32b06a0dc500ba462c1eebe7e34e73497c` 完成以下修复：

- 新增 `runs-outputs` source，root 为 repository `runs/`，layout 为 `run_outputs`；
- scanner 只读取 direct `runs/<run_id>/output/**`、`runs/<run_id>/outputs/**` media 与同 workspace
  `sidecars/**`、`evidence/**`，排除
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

### Seedance V3 Runtime Evidence

当前最新 skyship composition 是两个 Seedance Shot 经本地 `ffmpeg` 合成的 review derivative，不是新的
Seedance Provider raw output：

- `runs/seedance-mini-r2v-epic-skyship-20260829-002/output/epic-skyship-two-shot-29p79s-no-caption-bgm-v3.mp4`
  - bytes: `20143672`
  - SHA-256: `00b6bce620ab5af929607457d257fb6f812f4503cd133ff6b99e0a212b247471`
  - `FINAL_ACCEPTANCE=NOT_EVALUATED`；没有独立 human verdict；
- `runs/seedance-mini-r2v-epic-skyship-20260829-002/output/epic-skyship-two-shot-29p79s-small-caption-voice-bgm-v3.mp4`
  - bytes: `19828969`
  - SHA-256: `35d385483ef96da349d7ab161faae59d13777268f5b4199cc814638aed122093`
  - explicit human playback finding 与 `FINAL_ACCEPTANCE` 均为 `FAIL`。

Live catalog 将两条记录投影为 `bound + deterministic_composition`，默认 `linked` filter 可见。Chrome 在
`AI-VIDEO Runs Outputs` source 中清除旧 query 后显示两张卡片；打开 no-caption 分支时 opaque media token
`readyState=4`、`duration=29.791667`，页面显示 exact repository-relative path 与 SHA。

### Seedance V4 Evidence Extension

Commit `b8830a8` 将同一 External catalog contract 扩展到最新 `review-v4/gate.json` technical review
candidate。目标 MP4 由另一个已完成的 media session 创建；本次只修复 read-only frontend/server projection，
没有重新生成 Seedance Shot、旁白或 composition：

- path: `runs/seedance-mini-r2v-epic-skyship-20260829-002/output/epic-skyship-two-shot-29p79s-consistent-voice-bgm-v4.mp4`；
- bytes: `19880554`；
- SHA-256: `fb4d626ff7af31add575583c181359ad4237bf43c802600bef041cbeb84dd7f5`；
- measured playback duration: `29.791667` seconds；
- exact evidence: `runs/seedance-mini-r2v-epic-skyship-20260829-002/evidence/review-v4/gate.json`。

V4 adapter 只在 artifact path、SHA-256、bytes、same-run evidence containment、
`review_candidate_gate=PASS`、`FINAL_ACCEPTANCE=NOT_EVALUATED` 与 explicit acceptance boundary 全部匹配时
投影 `bound + deterministic_composition + technical_gate=PASS`。它明确保留
`human_verdict=null`、`lifecycle_status=NOT_EVALUATED` 与 `evidence_classification=non_canonical`；不产生
candidate activation、P6、Final Acceptance 或 human acceptance。错误 SHA、bytes、traversal path、越界
acceptance 字段均 fail closed；同一 exact bytes 同时出现 V3/V4 binding 时标记 association ambiguity，不按版本
或 mtime 猜测。

Live `/api/external-media?refresh=1` 返回上述 exact projection。Chrome 默认 `已关联` filter 中可见该卡片，
播放器 opaque token 的 `readyState=4`、`duration=29.791667`，detail 显示 exact path、full SHA 与
`evidence/review-v4/gate.json`。

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

Seedance extension 的 current verification：

- Provider Console Node/continuity suite：`86 passed`；
- `npm exec --offline -- vite build`：PASS，`4582 modules transformed`；
- native `reviewer_xhigh` final scoped re-review：`accept`，无 blocking/non-blocking concern；
- exact commit range `8c3e33c^..8c3e33c` 的 mandatory Harness checks 全部通过，包括
  skill boundary `2 passed`、Architecture Gate PASS、Provider Console Python `42 passed`、Node `86 passed`
  与 web build；
- fresh passing receipt：`.agent/harness/runs/provider-console-seedance-output-20260830-v2/receipt.json`；
  verifier 的 `passed`、`fresh`、`fresh_for_snapshot`、`scope_paths_match`、`scope_worktree_clean`、
  `complete_completion_proof`、`integrity` 与 `artifact_integrity` 均为 `true`。

第一次 Harness attempt 使用 repository `.venv/bin/python`，因该环境缺少 `pytest` 产生 failed receipt
`.agent/harness/runs/provider-console-seedance-output-20260830-v1/receipt.json`；随后使用现有
`/home/reggie/miniconda3/bin/python` 对同一 immutable commit range 完成上述 passing verification，未安装 dependency。

Seedance V4 evidence extension 的 current verification：

- focused V4 regression：`1 passed`；Provider Console Node/continuity suite：`87 passed`；
- `npm exec --offline -- vite build`：PASS，`4582 modules transformed`；
- native `reviewer_xhigh` scoped re-review：`accept`，无 blocking/non-blocking concern；
- exact commit range `b8830a8^..b8830a8` 的 mandatory Harness checks 全部通过，包括 docs contract、policy
  audit、skill boundary `2 passed`、Architecture Gate PASS、Provider Console Python `42 passed`、Node
  `87 passed` 与 web build；
- fresh passing receipt：`.agent/harness/runs/seedance-review-v4-visibility-20260830/receipt.json`；receipt verifier
  的 `passed`、`fresh`、`fresh_for_snapshot`、`scope_paths_match`、`scope_worktree_clean`、
  `complete_completion_proof`、`integrity` 与 `artifact_integrity` 均为 `true`。

## Boundaries And Remaining Risk

- `runs-outputs` 是 External/non-canonical catalog，不改变 canonical Runs latest-follow。
- 文件名、mtime 或目录位置不会生成 Prompt、Shot、success、candidate 或 lifecycle truth；只有窄 schema 的 exact
  evidence chain可投影 composition review status。
- 未调用 Provider、未生成媒体、未修改 Manifest 或 activation state。
- 本次 `retrieve-ai-video-memory` experience query 成功返回 tagged last-good fragments；相关 experience shard
  标记为 stale 并由 CLI 排队 detached refresh，没有 foreground rebuild，也没有把 RAG hit 当作 runtime truth。
- Automatic `distill-ai-video-learning` evaluation outcome：`no_candidate`。V3/V4 属于同一
  `architecture_implementation` integration topic 的 schema/version 演进，不是可独立计数的 media experiment
  attempts；该记录保持 `learning_eligibility: ineligible`，不创建 placeholder。
- Implementation 与 record 均为 local commits；未 push、deploy 或 release。

## Agent Guardrails

- 不得把 `runs-outputs` 卡片当成 Production attempt 或 delivery truth。
- 不得把 technical `PASS_FOR_HUMAN_REVIEW` 覆盖 human `FAIL`。
- 不得扩大 layout 到 arbitrary recursive `runs/` scan；只允许 direct top-level `output/**` / `outputs/**`，
  nested Production render 必须继续排除。
- 不得对 unknown composition schema 或未知 verdict 字符串做 best-effort 解释。
