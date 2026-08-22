# Shot Continuity Execution-Stack Materialization Record

Date: 2026-08-23

## Purpose

记录 Phase P1 candidate-neutral Implementation I1 的 execution-stack materialization/reseal owner。Canonical contract 仍由 `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`、`docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md` 与 `docs/record_for_agent/2026-08-23-shot-continuity-experiment-contract.md` 拥有；本记录不授权 M0 submit、Provider、媒体生成、activation、push 或 release。

## Current Runtime Truth

- `ExecutionStackMaterialization` 以 candidate-neutral 的 profile/compiler/workflow bytes 计算并验证 exact SHA-256；claimed hash 与 supplied bytes 不一致时 fail closed。
- `GenerationExecutionStackIdentity.materialize()` 只允许 unmaterialized → materialized transition，生成新的 `execution_stack_hash`；已 materialized stack 发生 hash drift 时拒绝。
- `materialize_p0_qualification()` 是唯一 materialization/reseal owner。它会 reseal execution-stack-dependent qualification inputs、transition policies、validation set 与 prepared receipt，并重新建立 Manifest pointer。
- materialization source bytes 先以 `state/video-qualification/execution-stack-sources/{profile,compiler,workflow}/<sha256>.bin` content-addressed immutable artifacts 持久化，再推进 Manifest pointer；普通 materialized reopen、guarded reopen 与 recovery 都会 no-follow reopen 并重新计算 exact SHA-256。
- Recovery 将 selected source artifacts 报告为 `ACTIVE`，将 Manifest 推进前已完整 promotion 的 source artifacts 保留为 `ORPHAN_PRESERVED`；缺失、tamper、swapped bytes 与 symlink 都 fail closed。
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

Commit `79ce66a` 继续关闭 source-byte durability 与 recovery seam：

- 新增 `src/ai_video/production/execution_stack_materialization.py`，集中准备、去重、content-address 与 no-follow rehash exact profile/compiler/workflow bytes。
- `src/ai_video/production/_state_commit_p0_qualification.py` 在同一 immutable artifact batch 中先写 source bytes，再 reseal/推进 Manifest；exact replay 只重验 persisted sources，不产生写入。
- `src/ai_video/production/_state_commit_p0_recovery.py` 将 P0 orphan discovery 从 oversized shared recovery module 提取为 focused helper；`ProductionStateCommitter` approved MRO 未改变。
- `.agent/harness/policy.yaml` 与 `docs/agent-primary-contract-matrix.md` 同步新增 owner routing 与 human-readable invariant，没有修改 frozen Shot Continuity spec/plan。

该 commit 仍未提供真实 M0 Hybrid Stock20 profile/compiler/applicable workflow，也未接入 V1 effect-bound caller；因此它关闭的是 candidate-neutral owner 实现，不是 M0 submit gate 的 runtime evidence。

## Verification And Evidence

- Focused Shot Continuity suite：38 passed。
- Exact staged Harness receipt：`.agent/harness/runs/20260822T204701895399Z/receipt.json`，status `passed`；2570 production contract tests passed、3 skipped、680 deselected，CLI/config 13 passed，Shot Continuity P0 38 passed，Architecture Gate `PASS`（仅模块增长 warning）。
- Receipt 在 commit 前验证为 fresh、integrity、policy match、snapshot match、scope worktree clean；commit tree 与该 staged snapshot 一致。
- Native reviewer 使用 `gpt-5.6-sol`，第二轮 verdict 为 `accept with concerns`，blocking issues 为 0。剩余 concern 是后续 V1 必须重载并校验实际 runtime bytes，并强制 `require_materialized=True`。
- Source durability focused verification：structure + P0 `50 passed`；continuity/state/recovery 六文件矩阵 `331 passed`；`git diff --check` 与 compile check 通过。
- 第一份 exact staged Harness receipt `.agent/harness/runs/20260822T213443433929Z/receipt.json` 正确 fail closed：new source owner 未映射 policy，full suite 结果为 `1 failed, 3255 passed, 4 skipped`，唯一 failure 是 repository policy audit 的 unmapped path。
- Policy routing RED/green 后，Harness/docs focused tests `114 passed`；最终 exact staged Harness receipt `.agent/harness/runs/20260822T215623603457Z/receipt.json` 为 `passed`：Harness `127 passed`，Production contracts `2577 passed, 3 skipped, 680 deselected`，CLI/config `13 passed`，Shot Continuity P0 `45 passed`，Architecture Gate `PASS`（0 errors，2 个 oversized-growth warnings）。Receipt 在 commit 前验证为 fresh、integrity、policy match、snapshot match、scope worktree clean；receipt `index_tree` 与 commit `79ce66a` tree 均为 `2033c8bc476b76c7e146e00169e049e4b01b3d38`。
- Native `gpt-5.6-sol` high reviewer 对 source persistence/recovery verdict 为 `accept with concerns`、blocking issues 0；补充 interrupted-promotion orphan regression 后 scoped re-review 为 `accept`。剩余 concern 属于 V1：typed semantic/preflight validation 与 exact-hash immediate pre-effect consumption 尚未实现。
- MiniMax external CLI `MiniMax-M3` read-only explorer 首次返回了可用 findings，但 runner 原始 outcome 为 `status=error` / `PROTOCOL_ERROR`（`DONE_WITH_CONCERNS` 携带 non-empty questions）；bounded fresh retry 为 `status=success` / `DONE_WITH_CONCERNS`。Bounded writer 首次与 fresh retry 都因 permission-denial loop / exact grant policy denial 返回 `BLOCKED`，没有修改文件，随后按规则 fallback 到 main thread。自动诊断 capture：`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-e8b37295a8c49a97.md`。

## Assessment

I1 已关闭 candidate-neutral materialization/reseal owner 及其 exact source-byte durability/recovery 实现缺口，并证明 dependent evidence closure、normal/recovery rehash、tamper denial、orphan preservation 与 exact replay。它没有把 owner implementation 误报为真实 M0 materialization、submit-ready、Provider success、visual quality 或 Final Acceptance。

## Remaining Risks Or Next Work

- 真实 M0 non-Turbo Hybrid Stock20 profile/compiler/applicable workflow 仍不存在，当前 active P0 bundle 仍为 `unmaterialized`；M0 pre-submit gate 继续阻断 Validation V1。
- V1 submit 前必须完成 typed semantic/preflight validation、绑定 guarded reopen，并在 effect boundary 消费同一批 exact profile/compiler/workflow hashes；不能只信 opaque bytes 或 persisted hashes。
- 当前没有执行真实 materialization、M0 submit、T8 seed `320001` 或六 Shot baseline；这些仍按冻结实验顺序保持未执行。
- 本地 `main` 已提交但未 push；unrelated dirty/index work 保留且未纳入 I1 implementation commit。

## Agent Guardrails

- 不得通过 `record_p0_qualification_prepared()` 直接写入 materialized bundle。
- 不得以 Harness、hash、Provider capability 或 reviewer technical acceptance 替代 human visual acceptance。
- 不得把当前 record、plan 或 receipt 解释为 generation、activation、publication 或 release authorization。
