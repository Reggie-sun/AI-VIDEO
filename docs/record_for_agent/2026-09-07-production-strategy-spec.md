---
record_kind: architecture_implementation
topic_id: production-strategy-layer
learning_eligibility: ineligible
---

# Production Strategy Specification Record

Date: 2026-09-07

## Implementation Checkpoint — 2026-09-08

本节取代下文“尚未实现 / 等待同文件授权”的当前状态。用户已通过“实现”“继续”授权从当前
Generation Feedback staged 内容接续；其 index 保持原样，没有把既有 staged 工作认作本轮实现。

本轮新增 pure `ProductionStrategyResolver` 和 application `ProductionPlanningService`，从标准
Project reader、typed coverage、QA allocation 与 exact source-use evidence 产出生产候选，再由
原 committer materialize、原 composition 解析 timeline，只有缺失动态组件交回原 generation owner。
旧 `ShotVisualResolver.resolve()` 选择入口退役；历史数据读取、唯一 writer/timeline/P5/QA owners
保持原边界。实现细节与支持范围见 [contract matrix](../agent-primary-contract-matrix.md#production-strategy)
和 [runtime baseline](../v0.2-runtime-baseline.md#production-strategy--2026-09-08)。

Independent `reviewer_xhigh` 在多轮反例复现后接受 scoped implementation review。修复包括：
durable sibling evidence 排序、proof/stage 不降级、实际 composition window/transform/audio/caption
校验、历史 allocation policy 可重开但当前执行须复评、完整 QA pointer identity 校验、未受影响
authoring→asset edges 保留，以及 video begin/submit intent 前重验整个 production family 的素材资格。
Application caller 已移出 pure Planning 包，原 import boundary test 保留。

最终 focused suite 为 77 passed；Generation Feedback / Harness / boundary 组合为 325 passed，
Architecture Gate（`--base-ref HEAD`）为 PASS，保留既有 oversized-module warnings，没有刷新 baseline。
另有 157 项 service/reader/P5/generation-handoff/原 Planner tests 通过；reviewer 最后独立定向
15 项通过。完整 Production 回归（`tests -k 'production or video_candidate or video_generation'`）
为 3270 passed / 3 skipped / 1468 deselected，825.16 秒；该 suite 在最后几个复审修复前启动，
这些最终改动另由上述 77 / 325 项 fresh suites 重验，不能把组合结果称为一个 exact snapshot。
此前补充 suite 为
506 passed / 1 failed，唯一失败
是 application caller 位置，已由上述 157 项验证覆盖修复。中途运行和旧 snapshot 均不是正式验收。

现有 staged patch SHA-256 仍为
`28446000e8a82589d91133dc9c3bb08056ccbab82c5bcb15b4f2cb7410a4e34c`。
本轮代码保留为 unstaged overlay / untracked new files，未 stage、commit、push 或创建 worktree。
没有 Provider 调用、S01 媒体生成或新的 human/P6/Final Acceptance；offline fixtures 不证明实际
成片质量改善。尚无本轮 exact-snapshot Harness receipt，不能宣称正式 engineering closure。
剩余步骤是按 `AGENTS.md` Verification Contract 对 non-empty staged snapshot 使用 Harness 的
detached temporary worktree 验证；当前未扩展 worktree 授权或改动既有 index，待最终验证权限明确。

按 `record-ai-video-session` 更新同一主题记录，并执行 `distill-ai-video-learning` 评估：
`no_candidate`。这些是 deterministic implementation / regression evidence，没有新增独立媒体
attempt 或 controlled empirical comparison；不创建 Learning Claim，也不修改 adopted policy。

## Historical Implementation Handoff — 2026-09-07

用户随后明确要求“实现”，Spec 已更新为 `accepted`，`implementation_status` 仍为 `not_started`。
下文 Spec 编写阶段的 `proposed`、未授权实现与未刷新 RAG 描述保留为历史，不再代表本次交接。

只读实现映射确认：`models.py` 尚无 typed parent/component lineage；`domain_acceptance.py` 与
`_state_commit_video.py::_require_current_generation_acceptance` 仍要求候选使用当前全项目生成 rubric；
`generation_feedback.py::for_project.history` 按 exact Shot ID 找 latest/baseline。不能只新增一个
Planning 文件就宣称完成组件分配与父意图失败历史的 PS8/PS11 验收。
现有 `PreparedArtifact` / `StateCommitRequest` 提供复用原 writer 的交接方向；没有新 writer 或
Manifest layout 变更被本轮代码验证。

这些源码以及 contract matrix、runtime baseline、roadmap、Harness policy 已包含其他任务的 staged
变更。主线程重新核验 staged patch SHA-256 仍为
`28446000e8a82589d91133dc9c3bb08056ccbab82c5bcb15b4f2cb7410a4e34c`，tracked unstaged diff 为空。
已请求用户决定同文件接续 ownership；确认前不修改重叠文件，不用旁路实现回避该约束。
当前只修改本轮自身的 Spec/记录；没有源代码实现、implementation plan、Provider/media、commit/push。

`retrieve-ai-video-memory` 的一次 `experience` 查询正常返回 tagged stale advisory fragments，并由 CLI
自动排队本地 derived-index refresh；没有等待重建、重试或采用不相关命中作为实现证据。
精确代码关系由 codegraph 与直接源码核验；Harness explicit-path inspection 已确认相关检查路由，
不是 passing receipt。两位 native read-only agents 分别提供调用入口与契约边界证据；没有派发 writer。
Learning evaluation 仍为 `no_candidate`：没有新的独立 empirical evidence 或已验证 implementation。

## Historical Spec Scope And Status

用户在只读架构调查后要求编写 Spec。本轮新增
[Production Strategy Spec](../superpowers/specs/2026-09-07-ai-video-production-strategy-layer.md)
与本记录；Spec 为 `proposed`、`implementation_status: not_started`。
没有创建 implementation plan、修改代码、调用 Provider、生成/分析新媒体或修改 Production state；
没有 stage、commit、push 或创建 worktree。

当前基线为 HEAD `4a5dc29f1d7bcfd178e7ef7510b0aa592563d5e1` 加既有 staged
Generation Feedback 工作；该 implementation 不属于本轮，既有 staged/dirty 内容保持原样。
不因新增上游 Spec 而把现有生成闭环描述为不存在，也不认领它的实现或验证。

## Contract Decisions

Spec 的唯一新增决策责任是：选择导演意图的生产手段及组合；已决定生成后的候选、干预、Router
选择与执行继续由既有 generation owners 负责。现有 `ShotVisualResolver` 的同类选择责任须收敛，
保留 Product 不 import Planning/Dev、单一 `ResolvedTimeline`、原 committer/P5/P6/Gate 边界。

首个实现必须接通真实非生成出口及受允许的一对多 handoff，不能仅增加策略标签或 FFmpeg options。
Source/raw 与 assembly/final 要求沿用原 acceptance owner；合法重新分配需要显式 revision、保留旧
verdict 并重验新组合，不能事后删除 FAIL。失效旧 decision 不授权 effect，当前上下文可重新决策。

S01 仅作概念案例，保留点名广播、native audio 偏好、手部动作、锁机位与同框异常证明。
actual07 local preview 的音频时序改善不抵消后续人工手部否决。旧 rough-cut 的静图复用失败作为
反例，防止把“更多复用/更少生成”当普遍最优。详细 source/history anchors 只由 Spec 保存；
本轮没有为上述历史观察新增独立实验或媒体质量结论。

## Verification And Evidence Boundary

Harness `inspect --path` 对两个 task-owned 文档路由到 `documentation`，没有 unmapped/fallback
路径；explicit scope 的 `closure_eligible` 为 `false`。按该路由执行文档契约、policy audit、
runtime skill boundary tests 与新文件 whitespace/link 检查。

结果：`scripts.docs_contract_gate check --json` 为 `ok: true`；`scripts.agent_harness policy-audit`
无 diagnostics/unmapped/unverified；`tests/test_runtime_skill_boundary.py` 为 `2 passed`。
两个新文件的 18 个本地链接全部存在，frontmatter、whitespace 检查通过；既有 staged patch 的
SHA-256 与写入前一致，tracked unstaged diff 仍为空。

Native `reviewer_xhigh` 对 Spec 进行独立只读审查，初审无 blocking issue；两条关于合法 revision
和 stale decision 拒绝范围的建议已修正；同一 reviewer 的 scoped re-review 为 `accept`，
没有剩余 blocking issue 或新增 concern。审查只覆盖 proposed contract。

这些检查不构成 implementation、runtime、Provider、media Gate 或 P6/Final Acceptance 证据。
本任务文件保持未暂存，未使用其他任务的 staged snapshot，也未运行需要 detached worktree 的
formal Harness verification；没有新增 exact-snapshot Harness receipt。

## Learning And Retrieval

按 `record-ai-video-session` 完成记录后执行 `distill-ai-video-learning` 评估：`no_candidate`。
本记录是 architecture proposal，不是新的独立 attempt、controlled comparison 或 material empirical
claim update；不创建 Learning Claim placeholder，不修改任何 adopted policy/Skill/Gate。
沿用前序直接重开源码和历史文件的调查结果；没有刷新 RAG index，也没有把 advisory memory 当 runtime truth。
