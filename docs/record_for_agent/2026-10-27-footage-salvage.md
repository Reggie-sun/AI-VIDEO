---
record_kind: architecture_implementation
topic_id: footage-salvage-edit-or-regenerate
learning_eligibility: ineligible
---

# Footage Salvage Implementation Record

Date: 2026-10-27

## Runtime Truth

已扩展原 `ProductionStrategyResolver`、`ProductionPlanningService`、QA、component lineage 和 P6；没有新建 Director、Provider、timeline、Registry 或 lifecycle owner。入口及合同见 [Footage Salvage](../footage-salvage.md)，四个开源仓库的 pinned revision、采用规则和拒绝规则见 [Research And Architecture Audit](../research/2026-10-27-footage-salvage.md)。

`QaPolicy.production_salvage_reviews` 保存 exact Take 身份、七维观察、完整原速声画覆盖、缺陷、可用/保护区间、替代素材及候选理由。未审证据不能推进。十种 repair operation 可组合，实际执行仍受原 operation/adapter 能力约束；未支持的 V2V、mask 等返回 capability gap。

候选先验证叙事/动作/保护内容，再以逐维风险偏序比较；风险相同时优先较少生成，unknown 不自动降成低风险。成本分别记录 Provider、本地 render 和时间；没有依据的估计保持 unknown。必须保留的动作没有发生时，不能用裁切或后期名称冒充修复。

物化、生成准入及 composition 绑定同一 review/plan；删除 review 也不能通过重物化抹去义务。重复失败按 canonical GenerationExperience 中的实际 authored design 匹配，使用原帧时长解析器；仅改 Shot ID、seed 或 receipt 不能清零。确实改动动作、时长、对白、首帧或覆盖后，新设计可重新评估，旧失败和预算历史仍保留。

P6 对接点/Scene 要求检查 full_playback、1x、audio_reviewed 及当前 exact review request。before/after 复用原 baseline/outcome。只有 standard loader 重验当前 FinalAcceptance 并确认同一物化方案，报告才投影 VERIFIED；本任务没有任何作品达到该状态。

## Verification And Review

- 标准 persisted fixture 经 loader → prepare → materialize → composition；覆盖局部尾部裁切、结构性动作失败、保护停顿、替代 Take、TRIM + GENERATE_INSERT、exact source/review 漂移、未审声画及 Scene FAIL。
- 原生产策略与 salvage 组合回归：180 passed；后续 Harness round 2 中原策略 135 passed、salvage 46 passed。最新修复的决策与 review 回归：24 passed，包含 13/61 帧、Shot 改名、真实动作重设计和 canonical 生成准入拒绝。
- 关联的 final-output、no-regression、visual-quality、junction、generation-feedback 等 suite：259 passed。新增规则不改变原 source-use、UNKNOWN、permit 或预算边界。
- `python -m scripts.architecture_gate check --base-ref 2366ff2`：PASS，0 error/warning/info。文档合同、任务 diff-check 与新增模块/测试 Ruff 通过。
- Required native reviewer：`/root/salvage_review`，profile `reviewer_xhigh`，三轮。FS-001（陈旧/删除评估的生成旁路）、FS-002（重复失败与重设计匹配）、FS-003（成本优先于风险）均由 Parent 确认为有效并修复；第三轮 finding set 为空。Parent 核对第三轮 16 个受审文件 SHA 均无漂移。review 是静态独立验证，不是影片验收。

最终 staged 检查入口与记录：

- `.agent/harness/runs/footage-salvage-focused-final-20261027/receipt.json`
- `.agent/harness/runs/footage-salvage-related-final-20261027/receipt.json`
- `.agent/harness/runs/footage-salvage-full-final-20261027/receipt.json`

实际状态以各 receipt 为准，不从测试数量推断全量 PASS。历史失败保留在 `footage-salvage-focused-r2-20261027`、`footage-salvage-related-20261027`、`footage-salvage-full-20261027`。

## Repository Verification Blockers

继承的 Harness 问题仍未解决：`AGENTS.md` 超 document budget，导致 related/full 在 `agent_rules_check` 提前停止，完整 suite 尚未执行；`full_tests.covers_check_ids` 缺两个既有 check（`reference_planning_tests`、`authored_visual_revision_tests`），并有 9 个既有路径未映射。本任务新增的 salvage check 已纳入 focused/related/full 映射，没有放宽 Gate 或刷新 baseline。

这些失败不能被本任务的直接回归或 reviewer 意见替代。完整仓库回归/发布资格保持未通过；本次只交付有验证边界的工程 checkpoint。

## Publication And Ownership

用户明确允许在已被其他任务修改的 `.agent/harness/policy.yaml` 和 `docs/agent-primary-contract-matrix.md` 追加本任务内容，仅提交 owned diff。

并行窗口的 `1201937`（`all`）在开发途中纳入了首批任务实现和其它改动，随后 `ea2198a` 提交了另一任务的素材记录；本会话未创建这两个提交，不回滚历史，也不把其中的其它任务工作归为本任务交付。后续 checkpoint 仅提交本任务文件，按项目要求 push `main` 并核验 SHA，publication 结果在最终答复中报告。

## Evidence Limits

本任务 Provider 调用 0 次、生成费用 0；没有改写现有影片的审核结果，没有真实影片/人类接受证据。测试中的 observations 是明确的 fixture，不代表实际观看。真实使用仍需连续声画观察、逐 Shot MCP Gate、实际组装以及 P6/原速审看。`distill-ai-video-learning` 评估为 `no_candidate`；未创建经验推广 claim、未修改 memory、未刷新独立 RAG 索引。
