---
record_kind: architecture_implementation
topic_id: final-output-first-no-regression
learning_eligibility: ineligible
---

# Final-output-first / No-regression Implementation

Date: 2026-09-08

## Purpose And Boundary

用户明确授权将局部 timing PASS、整片 FAIL 的 objective substitution 根因落实为通用
工程约束；历史依据是 [S01 rejected preview](2026-09-08-jieshi-s01-human-gap-history-boundary.md#latest-checkpoint--freeze-preview-rejected-and-root-cause)。
本轮不使用操作名称黑名单，不执行真实 Provider、媒体生成/重处理或 S01/S02 Production mutation。

Review / Repair 是质量与证据 owner，`ProductionStateCommitter` 是唯一 writer，
`ResolvedTimeline` 仍独占时间线。替换的旧行为是只检查调用方保护子集、局部 failure
消失即 supported、以及未将 repair baseline 全部证据纳入 outcome/Final Acceptance。
不引入新的 Agent runtime、状态机、Provider 选择路径或 renderer。

## Implemented Contract

`final_output_contracts.py` 和 `final_output_review.py` 保存 immutable 要求与 pure 判断，
由现有 approval、实际 repair commit、outcome、review、reader、Final Acceptance 入口调用。
完整字段与兼容边界以 [contract matrix](../agent-primary-contract-matrix.md#final-output-first--no-regression) 为准。

- QA 固定用户目标版本、完整要求和 proof；同版本禁止删改，显式新版本保留旧失败。
- repair 固定原片、QA、全部 review pointers；执行前重新打开原始证据，已知违规方案拒绝。
- 新片需要自身 exact evidence；遗漏、陈旧、identity 不匹配、人类要求没有正常速度 proof
  均不能通过。无退化仍需原失败和完整要求全部 PASS。
- 显式 FAIL outcome 保存失败终局，后续 repair 可以继续；R2 不得用自身成片改写 R1 成功。
  同目标 Final Acceptance 要求旧 repair 均有终局、最新 repair 为 PASS。
- generation policy `/3` 绑定 QA-owned `final_output_goal`，拒绝删保护与原目标下替换 rubric。
  `profile_version` 变化不构成用户目标变化；旧 policy 可重放但不能用于新的 begin/submit。
- 新增空字段和默认 PASS outcome 省略序列化以保留历史 hashes；缺 baseline 的旧 approval
  不获得新的 repair 执行资格。原 `RepairAction` public import 保持兼容。

## Verification And Review

实现中先以反例验证原入口可局部通过，随后在真实 committer/loader fixtures 覆盖：
局部改善但全局退化、要求遗漏、baseline 替换、证据缺失/陈旧/错 identity、原失败未修复、
正常速度 human proof、新目标版本、R1 FAIL→R2 PASS、借后续结果改旧失败、全部满足正例。
真实 `VideoGenerationService.start` 覆盖 goal mismatch 零文件写入、缺 QA 的 typed error，
`for_project()` 正例证明 goal 来自已激活 QA 而非调用方 callback。Provider doubles 无实际外部调用。

提交前 focused generation/repair/history/output 组合 `79 passed`；新增入口测试后
`tests/test_generation_no_regression.py` 为 `12 passed`。这些运行有重叠，不相加为独立样本。
Architecture Gate PASS；`models.py` fan-out 14 是非阻断 INFO，导入只重导出原 RepairAction
及同责任契约，未新增 writer。Harness policy audit 无 unmapped/unreferenced/missing paths。

native `reviewer_xhigh` 独立审查最初拒绝 profile-only 目标豁免与失败终局死锁；两项已修正。
scoped 复审先为 `accept with concerns`，无阻断；提出的 missing QA 错误分类与真实 goal binding
测试补齐后，同级最终 scoped verdict 为 `accept`。Review 不替代本地 tests、Harness 或真实媒体验收。

正式验收使用 exact commit range，自起点 `b9fd7b5` 到本任务提交：
`python -m scripts.agent_harness verify --base-ref b9fd7b5 --head-ref HEAD --run-id final-output-no-regression-20260908`。
权威结果保存于 `.agent/harness/runs/final-output-no-regression-20260908/receipt.json`；
需以 receipt status、scope、artifact hashes 和 `verify-receipt` freshness 共同判定。
本文在运行前与实现一起封存，不预先宣称该 receipt PASS；最终执行结果由 receipt 独占。

## Publication And Evidence Limits

本任务仅作 local task-owned commit，不 push/release。无关 staged 的
`docs/record_for_agent/2026-09-08-production-strategy-harness-closure.md` 与
`tests/test_agent_memory.py` 保持原样，排除在本任务提交和 Harness 范围外。

确定性测试只证明证据契约被执行，不能证明整体观感、人类真实正常速度观看或 Final Acceptance。
旧 QA 未建模的完整成片要求不能凭此被推断为满足；方案评估者仍需如实提交已知违规。
Python 入口不拦截任意 task-local shell，Agent 仍受根 AGENTS 的同一成片优先原则约束。
撤回的 freeze 预览保持 FAIL，S01 仍需独立媒体修复与适用 Gate；本实现不恢复旧授权。

## Learning Evaluation

`record-ai-video-session`：recorded；`distill-ai-video-learning`：no_candidate。
本轮是工程实现与离线契约验证，没有新增可归因的独立媒体实验或 controlled multi-arm
证据，不创建 Learning Claim，不修改 Skill/Provider policy adoption target。
repository advisory memory preflight 无匹配结果且索引陈旧；未重建 RAG，未将历史检索当验收。
