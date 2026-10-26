# Shot Reference Planning Record

Date: 2026-10-27

## AOCI Supersession — 2026-10-27

下方 AOCI stopped/blocked 状态为实现交付时的历史事实，现由[后续维护记录](2026-10-27-aoci-cognition-maintenance.md)取代：19 个 stale 条目已更新，observe 变化经复核，官方 Verify/Check/Guide 已证明当前共享工作区 aligned。此更新不改变原工程回归限制、真实媒体未验收状态，也不证明远端 clean checkout 对齐。

## Implemented Boundary

本次新增规则已接入 Director/Canvas → VideoPlanner → neutral requirement → Router → native compiler → QA diagnosis。详细契约见 [Shot Reference Planning](../shot-reference-planning.md)，实现计划见 [plan](../superpowers/plans/2026-10-27-shot-reference-planning.md)。`GenerationIntent.reference_planning` 显式启用执行约束；历史缺省字段保持原序列化与执行路径，只输出 advisory 建议。

持久身份、商品、场景、风格参考与 Shot 内事件分开。规则根据组合语义和有序事件规划用途、数量、优先级及相对阶段，不按固定秒数增加图片。静态视觉沿原策略，动态及 HYBRID 按职责精选；商业 approved-first-frame 复用原审批链。复杂运动要求明确连续视频职责，精确图形交现有 composition owner；未支持的时刻绑定、多镜头控制或输入冲突明确阻断，不默认拆分连续镜头。

Provider Capability、Registry、loader、hash/seal、budget、permit、ProductionStateCommitter、ResolvedTimeline 和 QA acceptance 均保留原 owner。新增报告是派生数据，不创建第二执行事实来源。规则与建议不证明视频模型执行了意图。

## Review And Repairs

Parent 是唯一 writer；native `code_mapper` 提供入口调查，`review_reference` 使用 `reviewer_xhigh` 作 read-only 独立审查，无 nested delegation。

初审 tree `c204f6b93bd2c83aa44db16d3c03a58825b218e7` 的 REF-001～004 均由 Parent 确认：静态最终视觉被过滤、多角色覆盖遗漏、跨维度事件遮蔽、商业商品首帧未复用。第二轮 tree `46b36c2009252afaf009c24397ecea74568a304d` 确认 REF-003 的部分构图覆盖仍不充分，以及 REF-005 HYBRID 多余图片、REF-006 frame-count 时长漏检。均修复并添加实际 Planner/readiness 回归。

第三轮源码候选 tree `3e6b70b6f266a21c799b5fed6e6bafea9203a68a` 经同一 reviewer 复审，finding set 为空。reviewer 核对 exact hashes，并通过只读断言复核静态资产保留、逐角色覆盖、组合语义、HYBRID 精选和 frame-count 边界。Parent 确认已知 blocker 全部关闭；此 tree 不包含本记录，仅绑定当前代码、测试、契约说明和计划。

## Verification And Evidence

- 当前源码关联回归：473 passed，覆盖新规则、Canvas authoring/loader、Planner/readiness、neutral requirement、Router、compiler 准备和 QA feedback；fake Provider 的 submit/fetch 均为零。
- 更广的 generation-feedback 映射检查：261 passed、2 failed 后停止。两个失败为 `test_cross_provider_canvas_reopen_after_paid_intent_uses_consumed_lineage`（Seedance compiler/4 新文本 QA 要求）和 `test_runtime_repair_requires_runtime_failure_evidence`（错误信息期望不匹配）。在未包含本任务改动的 `git archive 1c3a39677827542f2e4c5b013415b1b0136af7b9` 中逐项复现相同失败；未修复无关基线。
- Architecture Gate 相对 HEAD 为 PASS，既有大模块入口增量为 WARN；新规则职责置于独立小模块，没有改 baseline。
- related/full Harness 均在未修改的 `AGENTS.md` 文档预算超限处失败。该文件 blob 与 HEAD 都是 `4a393ce52ac0268f912fd33eafc64187f879ab62`。全量 pytest 没有被 Harness 执行，不能称完整回归通过。
- 独立 policy-audit 还发现 7 个既有未映射路径、3 个未引用测试；与 clean HEAD 导出逐项一致，本次新增路径没有增加这些缺口。
- 最终 staged Harness receipt 归 `.agent/harness/runs/reference-planning-delivery-related-20261027/receipt.json` 与 `reference-planning-delivery-full-20261027/receipt.json`；它们记录失败和具体跳过项，不能当作发布质量 PASS。

没有真实 Provider 或付费调用，没有新生成媒体。模型最终视觉质量、物理时序、逐 Shot 媒体 Gate 和人工验收均为 `NOT_EVALUATED`。

## Tooling And Publication Boundary

用户授权独立 worktree 隔离验证，并允许 policy/matrix/compiler 的本任务 hunks 与并发修改分别提交。隔离目录为 `/home/reggie/vscode_folder/AI-VIDEO-reference-planning`；主树其他任务的未提交内容必须保留。完成后仅提交 owned diff，push main 后回读远端 SHA；publication 状态以 Git 实际回读为准。

AOCI 已完整交付 33 条索引并确认传输；索引 dirty/stale，strict attestation 未通过，不能声明当前系统认知可靠。最终 `aoci_maintain` 返回 `stopped/blocked`，19 个跨任务 stale targets、803 个 observed pending，未签发可写 candidates；没有 pending transaction、recovery 或正式索引写入。未盲目 acknowledge 未审阅的全仓 scope；实际实现依据当前源码与测试，不因 AOCI advisory 改变 Product truth。

本记录使用 `record-ai-video-session`；自动 `distill-ai-video-learning` 评估为 `no_candidate`：工程 fixtures 不构成独立真实媒体实验，没有新增或采纳模型质量 Learning Claim。没有刷新 RAG 索引。
