# Caption Quality Gate Implementation Plan Record

Date: 2026-08-28

## Purpose

本文记录字幕专项质量 Gate 的 accepted implementation plan checkpoint。计划基于当前代码、
P6/Final Acceptance ownership、project memory 检索、成熟字幕 QC prior art 与独立
`reviewer_xhigh` 审查收敛。

本记录只证明实现边界、迁移顺序与验证契约已经形成可执行计划；它不证明字幕 Gate 已实现、
Manifest 已迁移、任何媒体已通过字幕质量验收，也不构成 Provider、media generation、P6 或
Final Acceptance authorization。

完整计划位于：

`docs/superpowers/plans/2026-08-28-ai-video-caption-quality-gate.md`

## Accepted Architecture Direction

计划将字幕专项 Gate 纳入既有 P6 review lifecycle，而不是新增第二个 top-level coordinator、
Manifest writer 或 Final Acceptance owner：

```text
CaptionTrack
  -> ResolvedTimeline.caption_cues
  -> HyperFrames exact final render bytes
  -> QaLayer.CAPTION evidence and adjudication
  -> existing Universal Quality Gate
  -> existing Domain Gate
  -> ProductionStateCommitter Final Acceptance
```

主要 contract decision：

1. 新增 `QaLayer.CAPTION`，由新的 cohesive caption-quality module 独占 requirement-level
   adjudication；`review.py` 只负责委派。
2. 保持 `CaptionTrack` 为 authored caption truth、`ResolvedTimeline` 为唯一 timing owner、
   HyperFrames 为 selected renderer、`ProductionStateCommitter` 为唯一 durable lifecycle owner。
3. 采用六个 finding groups：`SOURCE_INTEGRITY`、`TIMING_CONTRACT`、
   `RENDER_COMPLETENESS`、`LAYOUT_READABILITY`、`AUDIO_SEMANTIC_SYNC` 与
   `UNINTENDED_TEXT`。
4. 每个 required finding 独立输出 `PASS | FAIL | NOT_EVALUATED`；只有全部 required
   findings 为 `PASS` 才能聚合通过，且 `FAIL` 优先于缺证据产生的 `NOT_EVALUATED`。
5. `UNINTENDED_TEXT` 必须绑定 whole-render temporal/spatial coverage；只检查预期 cue 窗口
   不能证明没有 double-burn、残留字幕或其他非预期文字。
6. 新 caption-aware policy 使用 per-track language/delivery policy；不使用一个未经选择的
   universal CPS/CPL threshold 覆盖中文、英文、双语与 kinetic typography。
7. 新 policy 下 caption-specific overflow/readability 由 `CAPTION` 独占；historical policy
   仍可按旧 `LAYOUT` payload reopen，避免两个 active verdict owner。
8. caller-supplied `CAPTION PASS` 不得进入 authoritative closure；canonical coordinator 必须
   通过 private trusted adapter 从 exact active project/render/timeline/context/evidence 重建并判定。

## Schema And Compatibility Decision

计划明确采用 Manifest `2.15`，而不是把新增 caption state 当作无版本的 additive field：

- 新增 `manifest_schema.py` 作为 named Manifest capability/version set 的单一 owner。
- `2.15` 明确继承全部 `2.14` capabilities，并增加 caption-aware policy/context/receipt
  capability。
- Artifact schema 迁移至 `2.1`；`FinalAcceptanceReceipt` 与 `RepairOutcomeReceipt` 同步支持
  `2.1`。
- standard reader 必须拒绝 implicit migration、downgrade 与 mixed state；即使没有 CAPTION
  receipt，只要 Manifest `2.14` 指向 caption-aware `QaPolicy 2.1`，也必须 fail closed。
- strict reopen 必须重载 exact project/request/context/evidence，调用同一个 caption adjudicator
  重新计算 verdict，并要求 recomputed verdict 与 stored receipt verdict 完全一致。

该 migration 仍只是计划；当前 runtime schema 未在本任务中改变。

## Review History

首次 `reviewer_xhigh` 审查给出 `reject`，指出四个 blocking issues：

1. 缺少 Manifest/container version bump。
2. caller-supplied `CAPTION PASS` 存在 bypass 风险。
3. project/Final Acceptance 的 request/context strict reopen 不完整。
4. cue-only coverage 无法证明不存在 unintended text。

计划随后加入 Manifest `2.15` migration、private trusted P6 adapter、完整 strict reopen 与
whole-render unintended-text coverage。第二轮审查提出的 Harness mapping、Manifest `2.14`
policy-only mixed-state rejection 与 verdict recomputation concerns 也已补齐。

最终 scoped re-review verdict 为 `accept`，无 blocking issues 或 non-blocking concerns。

## Verification And Publication State

- Plan commit: `5f10004` (`docs: plan caption quality gate`)。
- Exact base commit: `58f16634a4ef0d574d18c9707fedc8d430013230`。
- Exact commit-range Harness receipt:
  `.agent/harness/runs/20260828T114543693474Z/receipt.json`。
- Receipt verification: `passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`complete_completion_proof=true`、`snapshot_matches=true`、
  `workspace_cleanup_confirmed=true`、`workspace_stable_confirmed=true`。
- Harness selected `scope_diff_check`、`docs_contract_check`、`policy_audit_check` 与
  `product_runtime_skill_boundary_tests`; boundary tests reported `2 passed`。
- `git diff --check` passed。
- Commit is local `main` only；未 push、未 release。

本任务没有修改 Product Runtime、tests、Manifest、P6 policy、caption assets、media、Provider
state 或 Final Acceptance state；没有执行 OCR、ASR、waveform/media analysis、live/paid
Provider call 或 human final-media review。工作区中其他 staged/dirty files 均保留，未纳入本任务
commit。

## Implementation Boundary

后续只有在获得 implementation authorization 后才执行计划。实施前必须重新检查 current code、
Git state、live writers 与 exact target-file ownership，尤其是 `.agent/harness/policy.yaml`、
contract matrix、runtime baseline 与 roadmap 的 same-file overlap。

实施需要保持以下 unchanged contracts：

- 不新增 renderer fallback、timeline owner、Manifest writer 或 automatic activation path。
- OCR、ASR、waveform、frame sampling 与 renderer telemetry 只产生 raw evidence，不拥有
  canonical caption truth 或 Production verdict。
- evidence 缺失、陈旧、identity mismatch、coverage 不完整或 evaluator unsupported 时必须
  `NOT_EVALUATED`，不得静默 PASS。
- rerender、caption/audio/timeline identity 变化必须使旧 CAPTION receipt 与 Final Acceptance
  stale。
- empirical subtitle quality 仍需要 exact final-media evidence；unit tests、Harness 或 plan review
  不能替代 human/perceptual acceptance。

## Agent Guardrails

- `CaptionTrack` valid 不等于 final rendered captions correct。
- `QaLayer.LAYOUT PASS` 不等于字幕准确、同步、完整或无重复烧录。
- 计划获审查接受不等于 implementation 完成。
- Manifest migration 设计完成不等于 current reader 已支持 `2.15`。
- Harness documentation receipt 不等于 runtime、media、P6 或 Final Acceptance evidence。
- 未重新核对 implementation-time dirty ownership 前，不得修改潜在重叠文件。
