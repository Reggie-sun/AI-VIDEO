# Shot Continuity Execution-Stack Materialization Record

Date: 2026-08-23

## Purpose

记录 Phase P1 candidate-neutral Implementation I1 的 execution-stack materialization/reseal owner。Canonical contract 仍由 `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`、`docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md` 与 `docs/record_for_agent/2026-08-23-shot-continuity-experiment-contract.md` 拥有；本记录不授权 M0 submit、Provider、媒体生成、activation、push 或 release。

## Current Runtime Truth

- `ExecutionStackMaterialization` 以 candidate-neutral 的 profile/compiler/workflow bytes 计算并验证 exact SHA-256；claimed hash 与 supplied bytes 不一致时 fail closed。
- `GenerationExecutionStackIdentity.materialize()` 只允许 unmaterialized → materialized transition，生成新的 `execution_stack_hash`；已 materialized stack 发生 hash drift 时拒绝。
- `materialize_p0_qualification()` 是唯一 materialization/reseal owner。它会 reseal execution-stack-dependent qualification inputs、transition policies、validation set 与 prepared receipt，并重新建立 Manifest pointer。
- `record_p0_qualification_prepared()` 拒绝任何包含 materialized candidate stack 的输入，避免绕过 materialization owner。
- M1 Hybrid artifact 仍显式为 `presence="absent"`、`content_hash="none"`；没有 winner-specific child、fallback、final capability 或 activation。

## Session Work And Decisions

Commit `35ad154` 将 owner、hash binding、reopen guard、tamper/drift denial、exact replay 与 regression coverage 落地到：

- `src/ai_video/production/video_execution_stack.py`
- `src/ai_video/production/video_transition.py`
- `src/ai_video/production/_state_commit_p0_qualification.py`
- `src/ai_video/production/__init__.py`
- `tests/test_production_p0_qualification.py`

本窗口没有调用 Provider、ComfyUI、网络或媒体生成；当前 M0 仍保持零 effect，真实 V1 pre-effect caller 尚未接入 guarded reopen。

## Verification And Evidence

- Focused Shot Continuity suite：38 passed。
- Exact staged Harness receipt：`.agent/harness/runs/20260822T204701895399Z/receipt.json`，status `passed`；2570 production contract tests passed、3 skipped、680 deselected，CLI/config 13 passed，Shot Continuity P0 38 passed，Architecture Gate `PASS`（仅模块增长 warning）。
- Receipt 在 commit 前验证为 fresh、integrity、policy match、snapshot match、scope worktree clean；commit tree 与该 staged snapshot 一致。
- Native reviewer 使用 `gpt-5.6-sol`，第二轮 verdict 为 `accept with concerns`，blocking issues 为 0。剩余 concern 是后续 V1 必须重载并校验实际 runtime bytes，并强制 `require_materialized=True`。
- MiniMax explorer 为 external CLI `MiniMax-M3`、read-only mapping，原始 outcome 为 `status=success` / `DONE_WITH_CONCERNS`。自动诊断 capture：`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-e8b37295a8c49a97.md`。

## Assessment

I1 已关闭 candidate-neutral materialization/reseal 的实现缺口，并证明 dependent evidence closure、tamper denial 与 exact replay。它没有把 materialization 误报为 M0 submit-ready、Provider success、visual quality 或 Final Acceptance。

## Remaining Risks Or Next Work

- V1 submit 前必须绑定 guarded reopen，并在 effect boundary 使用同一批 exact profile/compiler/workflow bytes；不能只信 persisted hashes。
- 当前没有执行真实 materialization、M0 submit、T8 seed `320001` 或六 Shot baseline；这些仍按冻结实验顺序保持未执行。
- 本地 `main` 已提交但未 push；unrelated dirty/index work 保留且未纳入本记录或 I1 commit。

## Agent Guardrails

- 不得通过 `record_p0_qualification_prepared()` 直接写入 materialized bundle。
- 不得以 Harness、hash、Provider capability 或 reviewer technical acceptance 替代 human visual acceptance。
- 不得把当前 record、plan 或 receipt 解释为 generation、activation、publication 或 release authorization。
