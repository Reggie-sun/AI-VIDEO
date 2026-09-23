---
record_kind: architecture_implementation
topic_id: ecommerce-production-job-m0-m3
learning_eligibility: ineligible
---

# Ecommerce Production Job M0–M3 Implementation Record

Date: 2026-09-19

## Supersession Notice — 2026-09-24

本文件下方的 M0–M3 状态和“M4–M7 尚未实现”边界只描述当时的 checkpoint。
M4–M7 offline implementation 已提交至 `f4f0dc4`，当前代码与验证状态见
[M7 Offline Code Record](2026-09-19-ecommerce-production-job-m7-offline-code.md)。
新证据仍不包含真实商品广告媒体、Provider submit、Production activation 或人工视觉验收。

## Purpose

记录 `EcommerceProductionJob` 首个 implementation slice 的当前 runtime truth、视觉合同决策、
exact-snapshot verification 与未实现边界。本记录取代 architecture audit 中 M0–M3 仍为
docs-only proposal 的状态，但不将工程验证提升为视觉成片、Provider 或 Final Acceptance 证据。

Canonical design sources：

- `docs/superpowers/specs/2026-09-19-ai-video-ecommerce-production-job.md`
- `docs/superpowers/plans/2026-09-19-ai-video-ecommerce-production-job.md`
- `docs/record_for_agent/2026-09-19-ecommerce-ad-architecture-audit.md`

## Current Runtime Truth

M0–M3 现在提供：

- `ecommerce_job_contracts.py` 的 strict、frozen、content-addressed handoff、request、projection、
  blocker 与 next-action contracts。
- 相互独立的四个视觉输入：技术交付 `EcommerceDeliveryProfile`、已审核视觉系统
  `EcommerceVisualSystemProfile`、每条广告 exact `EcommerceLayoutPlan` 与只绑定 exact hashes 的
  `EcommerceProductionCompileProfile`。
- Skill-side `export_runtime_handoff.py` 只做 pure/no-write export，要求 exact Shot/copy/product-presentation
  coverage、typography、safe area 与 keyword-emphasis binding，并保留 Product Truth、claim lineage
  和 unresolved capability/product-integration gaps。
- `ecommerce_job_compiler.py` 只编译 existing sealed artifacts 与 asset-free Registry bundle；唯一写入
  adapter 只调用 `ProductionStateCommitter.bootstrap_initial_state()`。
- `ecommerce_job.py` 的 `inspect()` 从 strict reopen 的 Project / Registry / Manifest 推导
  `BOOTSTRAP_PROJECT`、`PREPARE_REFERENCES`、ordered generation frontier、composition/review frontier
  或 typed blocker；不持久化第二份 Job lifecycle truth。

Asset readiness 不接受 ID-only：要求登记 bytes 的 exact SHA-256 与 size。Commercial renderer 当前
只支持 pinned `sans-serif`，因此 typography token fail closed 到该 family，不虚报 custom brand font。

## Visual Assessment Boundary

这次实现不是单纯为了“工程正确”：它取消 generic layout defaults，并将安全区、字号、
字重、颜色、关键词强调、beat role、product presentation 和 protagonist 都变成每条广告可审核的
exact input。这使 runtime 能拒绝一套模板套所有 SKU、自动发明主角或丢弃物理交互 gap。

但 M0–M3 没有生成或渲染真实成片，也没有 integrated visual review。因此只能说“视觉决策输入已
被正确建模且禁止 generic fallback”，不能说布局、节奏、商品突出度或整片观感已验收。

## Verification And Evidence

Task implementation commits：

- `e00a502` — Ecommerce Production Job foundation。
- `5e43178` — Harness routing and canonical docs。
- `f8f38ce` — matrix ownership placement correction。
- `17ae89c` — exact-runtime handoff schema correction。

Executable evidence：

- Exact archived `17ae89c` focused suite：`116 passed in 12.70s`。
- Exact commit-range Harness `6d63051..17ae89c`：
  `.agent/harness/runs/ecommerce-production-job-m0-m3-20260919-02/receipt.json`，status `passed`。
- Harness 主要输出：Production contract `3486 passed, 3 skipped, 1670 deselected`；Harness tests
  `238 passed`；Architecture Gate `PASS (0 errors, 0 warnings, 0 info)`；ecommerce job suite `20 passed`。
- 在 clean clone 对同一 receipt 进行 `verify-receipt`：`fresh=true`、`integrity=true`、
  `complete_completion_proof=true`、`scope_worktree_clean=true`。主工作树因用户既有 staged voice/S02
  changes 与四个 control-plane paths 重叠，本地直接复核的 `scope_worktree_clean=false`；本任务
  没有清理、stash、覆盖或提交这些改动。

第一个 Harness run
`.agent/harness/runs/ecommerce-production-job-m0-m3-20260919-01/receipt.json` 为 `failed`：它发现
checked-in handoff schema 在 dirty tree 生成时意外吸收了未提交 `voice_routing` 字段。`17ae89c`
从 exact committed runtime 重新生成 schema；第二个 run 取代第一个 run 作为 completion evidence。

## Remaining Risks And Next Work

- M4–M6 `advance_once()` effects、ordered generation、bounded repair、canonical render、whole-video QC、
  Final Acceptance 和 exact delivery packaging 仍未实现。
- 本次没有 Provider/network/media execution，没有生成广告成片，没有 human/subjective visual acceptance，
  也没有 push 或 release。
- 未解决的 physical product interaction、tracking/mask/occlusion/lighting/camera matching 仍必须
  保留为 gap，不得为了出片静默降级。
- 当前 dirty voice-routing work 若最终修改 shared `Shot` schema，其 owner 必须在自己的 exact commit
  中重新生成 ecommerce handoff schema；本任务不得预先提交该未完成 contract。

## Agent Guardrails

- 不得把 handoff/compiler/projection PASS 描述为已出片、好看、live-ready 或 Final Accepted。
- 不得新建第二个 Job Manifest、timeline、renderer、writer 或 activation owner。
- 不得用 generic visual defaults 替代 per-ad reviewed visual/layout contract。
- 不得丢弃 Product Truth、claim lineage、asset exact identity 或 unresolved capability gap。
