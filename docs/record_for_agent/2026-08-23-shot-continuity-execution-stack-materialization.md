# Shot Continuity Execution-Stack Materialization Record

Date: 2026-08-23

## Purpose

记录 Phase P1 candidate-neutral Implementation I1 的 execution-stack materialization/reseal owner。Canonical contract 仍由 `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`、`docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md` 与 `docs/record_for_agent/2026-08-23-shot-continuity-experiment-contract.md` 拥有；本记录不授权 M0 submit、Provider、媒体生成、activation、push 或 release。

## Current Runtime Truth

- `ExecutionStackMaterialization` 以 candidate-neutral 的 profile/compiler/workflow bytes 计算并验证 exact SHA-256；claimed hash 与 supplied bytes 不一致时 fail closed。
- `GenerationExecutionStackIdentity.materialize()` 只允许 unmaterialized → materialized transition，生成新的 `execution_stack_hash`；已 materialized stack 发生 hash drift 时拒绝。
- `materialize_p0_qualification()` 是唯一 materialization/reseal owner。它允许按candidate逐个materialize，将qualification inputs绑定到当前materialized stack hashes，reseal execution-stack-dependent transition policies、validation set与prepared receipt，并重新建立Manifest pointer；selected stack含absent component时fail closed。
- materialization source bytes 先以 `state/video-qualification/execution-stack-sources/{profile,compiler,workflow}/<sha256>.bin` content-addressed immutable artifacts 持久化，再推进 Manifest pointer；普通 materialized reopen、guarded reopen 与 recovery 都会 no-follow reopen 并重新计算 exact SHA-256。
- Recovery 将 selected source artifacts 报告为 `ACTIVE`，将 Manifest 推进前已完整 promotion 的 source artifacts 保留为 `ORPHAN_PRESERVED`；缺失、tamper、swapped bytes 与 symlink 都 fail closed。
- `record_p0_qualification_prepared()` 拒绝任何包含 materialized candidate stack 的输入，避免绕过 materialization owner。
- `reopen_m0_validation_preflight()` 是 candidate-neutral 的 M0 V1 pre-effect reopen owner：它从 canonical Project、Registry 与 prepared receipt 重载同一 bundle，要求 M0 已 materialized、M1 仍为 `unmaterialized` 且 Hybrid artifact 为 `absent` / `none`，重新验证 exact profile/compiler/workflow、frozen calibration 与全部 dependent evidence 的 stack binding，然后只返回 immutable `M0ValidationPreflightSnapshot`。该 snapshot 不写 durable intent、不 mint permit、不调用 Provider，也不授权 submit。
- Qualification-only M0 sources由`src/ai_video/production/shot_continuity_m0_qualification.py`与`workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_*`拥有：profile source bundle包含exact profile与binding bytes，compiler固定literal `Hybrid`四锚点mapping、frozen prompt hash、Stock20 `dual_clock_euler/native_flow`、20 steps与no-LoRA exact graph。
- Ignored rainy-station run root当前Manifest revision为`4`；active P0 receipt为`6a3c5516aa0b8dfdc70ee4660893c1a0e449742d719187dad965bf629d7c8cb2`，M0 stack为`2acf7e7843923460c503b6c9f3f53ca9c0bed627d21d8ca2cabe2e8e5b1a45f9`。M1保持原stack `4d08741636647fbb29f9cf69a69a2c81d62156cef128f619d26a17b72e94c01b`、`unmaterialized`与Hybrid artifact `presence="absent"`、`content_hash="none"`；没有 winner-specific child、fallback、final capability 或 activation。

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

Commit `bc088e9` 完成并实际执行M0-only qualification materialization：

- 新增offline-only `scripts/materialize_shot_continuity_m0.py`，只对frozen Project/Registry/P0 receipt/M0+M1 identities与calibration contract执行exact preflight和committer materialization；模块不包含transport、Provider submit或capability registration。
- M0 exact profile/compiler/workflow hashes分别为`0bbd8ff2e9976d91c0b7250512942c662ce551b4676cca4504734aff65b86491`、`d4af4843e5548a353e01a794d3752020c624be2d6012c4ba52bd5f5a91f85ecc`与`963bd91ad81ca102053deb08b29a7aa8fb6849a6256a78ccbfbc6138d7a855d2`；dependent qualification inputs、三个transition policies、validation set与receipt全部reseal并strict reopen。
- 同一canonical run上的第二次materialization返回完全相同hashes与Manifest revision `4`，证明actual exact replay没有重复Manifest advancement；tests另外验证file mtime/bytes zero-write。
- `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`与`docs/agent-primary-contract-matrix.md`将新script/module/test/workflow paths收敛到既有`shot_continuity_p0` owner，没有建立第二category或fallback control plane。
- `docs/v0.2-runtime-baseline.md`只把上述动态runtime evidence写为M0 materialization gate closure，明确没有把它升级为Validation V1、generation、winner、activation或acceptance。

Commit `c8eeb51` 关闭 Validation V1 在 M0 submit 之前缺失的 pre-effect reopen seam：

- 新增 `reopen_m0_validation_preflight()` 与 immutable `M0ValidationPreflightSnapshot`，把 exact source reload、materialized M0、unmaterialized M1、Hybrid absent、calibration 与 dependent-evidence closure 收敛为单一 read-only owner。
- owner 复用 `ProductionStateCommitter.reopen_p0_qualification_prepared(required_materialized_candidates=("m0",))`，不修改 generic `VideoGenerationService`，避免把 Shot Continuity M0 policy 错误施加到 H3、Hailuo、Seedance 或其他通用 caller。
- RED/green regressions覆盖 unmaterialized denial、materialized reopen、stack/source/dependent-evidence drift、reopen、tamper、exact replay，以及 workflow node ID/class swap；所有失败都发生在 durable intent、permit 或 Provider effect 之前。
- `.agent/harness/policy.yaml`、`docs/agent-primary-contract-matrix.md` 与 `docs/v0.2-runtime-baseline.md` 同步 owner、routing 和动态证据边界；frozen Shot Continuity spec、plan、prompt 与 rubric 未修改。

## Verification And Evidence

- Focused Shot Continuity suite：38 passed。
- Exact staged Harness receipt：`.agent/harness/runs/20260822T204701895399Z/receipt.json`，status `passed`；2570 production contract tests passed、3 skipped、680 deselected，CLI/config 13 passed，Shot Continuity P0 38 passed，Architecture Gate `PASS`（仅模块增长 warning）。
- Receipt 在 commit 前验证为 fresh、integrity、policy match、snapshot match、scope worktree clean；commit tree 与该 staged snapshot 一致。
- Native reviewer 使用 `gpt-5.6-sol`，第二轮 verdict 为 `accept with concerns`，blocking issues 为 0。剩余 concern 是后续 V1 必须重载并校验实际 runtime bytes，并强制 `require_materialized=True`。
- Source durability focused verification：structure + P0 `50 passed`；continuity/state/recovery 六文件矩阵 `331 passed`；`git diff --check` 与 compile check 通过。
- 第一份 exact staged Harness receipt `.agent/harness/runs/20260822T213443433929Z/receipt.json` 正确 fail closed：new source owner 未映射 policy，full suite 结果为 `1 failed, 3255 passed, 4 skipped`，唯一 failure 是 repository policy audit 的 unmapped path。
- Policy routing RED/green 后，Harness/docs focused tests `114 passed`；最终 exact staged Harness receipt `.agent/harness/runs/20260822T215623603457Z/receipt.json` 为 `passed`：Harness `127 passed`，Production contracts `2577 passed, 3 skipped, 680 deselected`，CLI/config `13 passed`，Shot Continuity P0 `45 passed`，Architecture Gate `PASS`（0 errors，2 个 oversized-growth warnings）。Receipt 在 commit 前验证为 fresh、integrity、policy match、snapshot match、scope worktree clean；receipt `index_tree` 与 commit `79ce66a` tree 均为 `2033c8bc476b76c7e146e00169e049e4b01b3d38`。
- Native `gpt-5.6-sol` high reviewer 对 source persistence/recovery verdict 为 `accept with concerns`、blocking issues 0；补充 interrupted-promotion orphan regression 后 scoped re-review 为 `accept`。剩余 concern 属于 V1：typed semantic/preflight validation 与 exact-hash immediate pre-effect consumption 尚未实现。
- M0 real-materialization focused/structure matrix最终为`77 passed`。Exact staged Harness receipt `.agent/harness/runs/shot-continuity-m0-materialization-20260823-v1/receipt.json`为`passed`，SHA-256 `f5875bf9b4a64d0afba1fdf593445b58dad8e214ca57496fe4e89e4152e5e596`：Harness `127 passed`、workflow `9 passed`、production state `950 passed`、Shot Continuity P0 `60 passed`，Architecture Gate `PASS`（0 errors，1个atomic owner oversized-growth warning）。Receipt在commit前验证artifact integrity、freshness、policy、snapshot、scope worktree clean、cleanup与closure全部为true；index tree `d6d47c0fff8ff131acf09edc9e0e7cd570c898ca`与reviewed snapshot一致。
- Native `gpt-5.6-sol` high reviewer首次发现M1 absent materialization bypass与target identity绑定不足并给出`reject`；修复M1-only denial、frozen target、binding durability、prompt与exact node/edge checks后scoped re-review和final exact-staged review均为`accept with concerns`、blocking issues 0。剩余non-blocking concern是为exact node swap/script target-negative branches补更直接的独立regression，以及atomic owner LOC warning。
- MiniMax external CLI `MiniMax-M3` read-only explorer本窗口首次因`NEEDS_CONTEXT`携带non-empty concerns返回`status=error` / `PROTOCOL_ERROR`；parent用pinned plugin `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`的literal `Hybrid`证据与M0-only/M1-absent contract完成bounded fresh retry，最终`status=success` / `DONE_WITH_CONCERNS`。它正确定位committer与missing qualification sources，但误读了unmaterialized source verifier，parent按代码证据修正。Sanitized captures：`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-e8b37295a8c49a97.md`与`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-b3dbe91ccbad6257.md`。
- M0 V1 preflight strict RED/green file最终为`10 passed`；两个focused文件为`19 passed`；Shot Continuity P0为`71 passed`；continuity/lifecycle/recovery扩展矩阵为`388 passed in 264.03s`；compile check与`git diff --check`通过。
- Exact staged Harness receipt `.agent/harness/runs/shot-continuity-m0-v1-preflight-20260823-v1/receipt.json` 为 `passed`，SHA-256 `eef4d9ab714aac99a9c6c2f1a8b81da2795aa573f4b02174becb9c4497706df3`；其index tree `8ec2cc055e2a9972f534d9b1c10a7453738a7dd9`与commit `c8eeb51` tree一致。Exact commit-range receipt `.agent/harness/runs/shot-continuity-m0-v1-preflight-commit-20260823-v1/receipt.json` 为 `passed`，SHA-256 `e40906548d4d4abdcdde5f7bec33f42022fd11095cf9dd3eeffedbd137275f0b`；创建时artifact integrity、freshness、policy、snapshot、scope cleanliness、cleanup与closure均为true。后续其他session推进local `HEAD`后重新验证该固定receipt会正确显示`fresh=false` / `snapshot_matches=false`，不改变其对exact commit range的历史证据边界。
- Native `gpt-5.6-sol` high reviewer verdict为`accept with concerns`，blocking issues 0。唯一material non-blocking concern是新增owner的直接测试使用duck-typed committer且只构造两个qualification inputs；既有real `ProductionStateCommitter` tests已覆盖bundle closure与tamper，但后续可补一个直接owner integration regression证明real reopen失败透传并保持filesystem byte/mtime zero-write。
- 本窗口 MiniMax external read-only explorer的Role为`explorer`、Scope为V1 pre-effect guarded reopen mapping、runner model为`MiniMax-M3` high、Claude-compatible transport，最终`status=success` / `DONE_WITH_CONCERNS`。它正确定位generic submit、committer和source seams，但建议把M0 guard无条件放入generic `VideoGenerationService.submit_once()` / `submit_local_once()`；parent根据callers与request schema证据拒绝该建议并建立M0-specific read-only owner。Sanitized capture：`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-7dcb1f9ab61750e0.md`。

## Assessment

I1 已关闭 candidate-neutral materialization/reseal owner、exact source-byte durability/recovery、真实M0 qualification source freeze与M0-specific pre-effect reopen owner，并在canonical rainy-station run上完成M0-only materialization、dependent evidence closure与exact replay。该evidence关闭的是M0 submit之前的execution-stack materialization和read-only preflight implementation gates，不是Provider success、视觉质量、winner、P6或Final Acceptance。

## Remaining Risks Or Next Work

- Validation V1仍未启动；下一步的effect-bound M0 caller必须在durable intent和submit之前调用`reopen_m0_validation_preflight()`并消费其exact snapshot。任何source、Project/Registry、candidate、prompt/calibration、dependent evidence或workflow drift都必须在submit前拒绝；仅成功构造snapshot不能被解释为submit authorization。
- 当前没有执行M0 submit、M1 build/materialization、T8 seed `320001`、六 Shot baseline或任何视觉验收；M1只有在M0按frozen gates失败且exact Hybrid artifact存在后才可能进入独立materialization/validation。
- 后续可补一个real `ProductionStateCommitter`直连的preflight regression，记录project tree bytes/mtime，证明exact replay zero-write并验证persisted source或dependent-evidence tamper通过该owner原样fail closed；这是review concern，不是当前blocking issue。
- 本地 `main`包含implementation commits `bc088e9`与`c8eeb51`，当前 `c8eeb51`已成为后续local commits的ancestor但尚未push；unrelated dirty/index work保留且未纳入这些commits。

## Agent Guardrails

- 不得通过 `record_p0_qualification_prepared()` 直接写入 materialized bundle。
- 不得以 Harness、hash、Provider capability 或 reviewer technical acceptance 替代 human visual acceptance。
- 不得绕过`reopen_m0_validation_preflight()`直接把prepared receipt或stack hash交给未来M0 effect owner；该read-only owner必须在durable intent之前执行，且其返回值本身不是permit。
- 不得把当前 record、plan 或 receipt 解释为 generation、activation、publication 或 release authorization。
