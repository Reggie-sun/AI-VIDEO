# Shot Continuity Experiment Contract Record

Date: 2026-08-23

## Purpose

本记录固化 2026-08-23 已收敛的 Shot continuity 实验顺序与判定边界，供后续 Agent 在不重新扩展 spec 的前提下执行。Canonical contract 仍由 `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md` 与 `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md` 拥有；本记录不复制完整 prompt，也不构成 Provider、媒体生成、付费调用、activation、push 或 release 授权。

本 checkpoint 只证明 documentation contract 已冻结并完成对应文档验证。它不证明 T8 长镜头能力、六 Shot 成片质量、P6 verdict、human GO 或 Final Acceptance。

## Current Contract Truth

- 实验顺序冻结为：先做 T8 32-second capability screen，再做单一 Provider/model 的 30-second six-shot baseline；只有 baseline 通过，才允许验证一个有业务价值且明确存在 hard cut 的 directed cross-provider pair。
- 本阶段不再讨论 ownership、fail-closed、no fallback 或 boundary-aware policy；这些既有边界保持不变。
- 每次实验开始前必须冻结 exact model/checkpoint/profile、reference、prompt、Shot contract、seed、resolution、sampling 与 PASS/FAIL rubric。实验中不得临时降低门槛、改 seed 规则或增加 fallback 来挽救路线。
- 实验结果可以反向修改 continuity policy、降级无效 obligation 或删除过度约束；不得为了维护既有设计而强迫 evidence 符合 spec。
- 当前未执行 Provider、媒体、网络或付费调用，未选择新的 canonical character reference，也未产生质量 verdict。

## Frozen Experiment Sequence

### 1. T8 32-Second Capability Screen

- 目的只回答：`ScenePlusIdentity + 22-frame latent context` 在本机 RTX 5090 与用户审美下是否值得继续。
- 场景约束为单角色、单场景、中等运动。
- 第一轮只运行 seed `320001`，只允许 `CONTINUE` 或 `STOP` 两种结论。
- `STOP` 时立即停止该长镜头路线，不追加 seed、不降低 rubric、不临时改变 resolution、sampling 或 context contract。
- `CONTINUE` 时才允许执行预先声明的 seeds `320002`、`320003`、`320004`。
- 冻结的 model-grid output 为 `770` frames at `24 fps`，即 `32.083333...s`。这是 deliberate out-of-envelope capability screen，不得描述为 exact `32.000s`，也不得描述为当前 OpenVideo 已支持的 normal Shot duration。
- 当前 `h3-video` production-facing profile 的已知 Shot duration 上限仍为 `15s`；本 screen 的通过也不会自动改变该产品合同。
- 长镜头路线 `STOP` 不自动否决 normal hard-cut baseline，因为两项实验回答不同问题。

### 2. Single-Provider 30-Second Six-Shot Baseline

- 六个 Shot 必须复用一个 exact Provider/model/checkpoint/profile/execution stack、一份 exact canonical reference bytes/hash、seed `20260823`、`1344x768`、`24 fps` 与同一 global continuity contract。
- 每 Shot native generation 为 `124` frames；canonical `ResolvedTimeline` 只取每 Shot 前 `120` frames，得到 exact `5.000s`。六个 Shot 合计 `720` frames，即 exact `30.000s`；用于相邻边界的 terminal evidence 是 frame `119`。
- S1 `ESTABLISHING_WIDE`：建立角色、站厅、服装、红色皮革 satchel、向 frame right 的运动方向。
- S2 `MEDIUM_TRACKING`：`HARD_CUT + FULL_CONTINUITY`，验证 S1 exit motion 到 S2 entrance motion、步速、screen direction 与 prop swing。
- S3 `INSERT_CLOSE_UP`：`HARD_CUT + IDENTITY_STYLE_CARRYOVER`，重点验证 satchel、黄铜扣、衣袖与从行走到静止的 motion settle。
- S4 `MEDIUM_CHARACTER_ACTION`：`HARD_CUT + FULL_CONTINUITY`，验证中景 identity、停步、抬眼和转头时的 face stability。
- S5 `CLOSE_UP_REACTION`：`HARD_CUT + IDENTITY_STYLE_CARRYOVER`，作为 identity-priority gate 验证近景 facial identity。
- S6 `SCENE_BOUNDARY_WIDE`：`SCENE_BOUNDARY + IDENTITY_STYLE_CARRYOVER`，从 hall 切到 platform，但 character、wardrobe、prop 与 visual style 必须延续。
- `IDENTITY/PROP_CARRYOVER` 与 `IDENTITY_PRIORITY` 只是实验语义标签，不新增 runtime boundary enum；它们映射到既有 `IDENTITY_STYLE_CARRYOVER` 并通过 required dimensions 表达。
- Baseline 只有在 single-Shot quality、同角色多 Shot、motion continuity、prop continuity、hard-cut continuity、scene carryover 与最终剪辑观感全部通过，且用户明确认为成片值得留下时才是 `PASS`。不得以平均分掩盖任一关键维度失败。

### 3. Directed Cross-Provider Follow-Up

- 只有 six-shot baseline `PASS` 后才能开始。
- 从六个 Shot 中选择一个真正有业务价值且明确存在 hard cut 的边界，例如 `T8 -> Seedance`。
- 只验证一个 directed pair，不建立 full provider matrix，不以 fallback 掩盖失败。

## Verification And Evidence

冻结文档前已完成离线合同检查：

- T8 screen prompt 含且只含一组 H3 three-field contract。
- Six-shot baseline 的六个 Shot prompt 各含且只含一组 H3 three-field contract。
- Timing math 已核对：`770 = 17 * 45 + 5`、`770 / 24 = 32.083333...s`、`124 = 17 * 7 + 5`、`6 * 120 / 24 = 30.000s`。
- Documentation Contract Gate 已通过。

对应 exact staged snapshot 的 Harness receipts：

- `.agent/harness/runs/shot-continuity-six-shot-baseline-20260823-v1/receipt.json`，status `passed`，receipt SHA-256 `c17ddb8137d526984bb311a530d20ef313d7f3a18fb5108ae39e9cc82d6b4445`。
- `.agent/harness/runs/shot-continuity-experiment-contract-20260823-v2/receipt.json`，status `passed`，receipt SHA-256 `e470f66b8f5d70db42b8e88596d6f030fc43c5c86576a7c86c50e46325855dc9`。
- 两份 receipt 在 commit 前均完成 artifact integrity、closure eligibility、freshness、policy match、snapshot match、clean scope worktree 与 workspace cleanup verification。
- Commit `76367b2be88ce13e95506a3db6d33c658d36d0f9` 的 tree 与 six-shot baseline receipt 的 index tree 一致；commit `f082980e77617fceb07ee323a71a7526548f43bf` 的 tree 与 route-kill screen receipt 的 index tree 一致。

这些 evidence 只覆盖冻结的 documentation snapshot，不覆盖任何实际生成结果或视觉质量。

## Assessment

当前最重要的决策是把“模型是否值得继续”和“正常 hard cut 能否做出愿意保留的作品”拆成两个独立实验。这样 T8 长镜头失败不会混淆 baseline 的价值，而 baseline 失败也不会被跨 Provider complexity 解释掉。单一 seed 的第一轮是 route-kill gate，不是统计性 benchmark；只有明显有希望时才扩到三组补充 seeds。

六 Shot baseline 同时覆盖单镜质量、角色 identity、motion、prop、hard cut、scene carryover 与成片观看体验，足以在投入 cross-provider matrix 前暴露主要创作风险。最终 verdict 必须来自实际观看，不得由 structural checks、hashes、Provider success 或 Agent 自报替代。

## Remaining Risks And Next Work

- 尚未冻结并 materialize 本轮实际使用的 exact Provider/model/checkpoint/profile/execution stack。
- 尚未为该米色风衣角色选择或生成 exact canonical reference image，并记录 bytes/hash。
- 尚未执行 T8 `770`-frame screen，因此没有 GPU compatibility、wall time、motion/identity quality 或 `CONTINUE/STOP` evidence。
- 尚未生成、裁切、拼接或观看 six-shot baseline，因此没有 baseline `PASS/FAIL`、P6、人类审美或 Final Acceptance evidence。
- 尚未选择或执行 directed cross-provider hard-cut pair。
- T8 screen 是 out-of-envelope experiment；即使视觉有希望，也需要独立产品决策才能改变当前 `15s` duration contract。

## Agent Guardrails

- 后续 Agent 必须先读取 canonical spec 与 plan 中冻结的完整 prompts 和 rubrics，本记录不能替代它们。
- 不得把本记录、Harness receipt、生成成功或分析器输出写成 visual acceptance。
- 不得在未获对应授权时执行 remote/paid Provider、push 或 release；local loopback execution 仍须遵守 repository 中现有 preflight、permit、committer、recovery 与 media verification gates。
- 不得因第一次结果不理想而修改 seed、resolution、sampling、reference、prompt 或 PASS/FAIL rubric；应按冻结规则停止或进入预声明的下一阶段。
- 当前 commits 仅存在于 local `main`；未验证或声明 `origin/main` publication。
- 本记录创建时保留 `.codex/hooks.json`、`index.json`、Seedance implementation/tests 与 `.workflow/.scratchpad/` 的既有 unrelated dirty work，未将其纳入本 checkpoint。
