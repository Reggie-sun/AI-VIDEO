# Sequence Continuity Research

## A. Current Real Path

研究基线为 `a0682cbdde8b494947cc9bc7ffcc147670cd7dc5`，初始 working tree 干净。
当前没有名为 Canvas 的 Product 数据模型或通用 Canvas runtime；Canvas 是 Agent authoring 方法。
`production/models.py::Story/StoryBeat` 保存故事 beats，`Storyboard/StoryboardBeat.shot_ids`
保存 authored Shot 顺序；`Shot` 保存 selected revision、scene/beat membership 和创作要求。
`project.py::load_production_project` 重开 Manifest-selected Project/Registry，
`validation.py::validate_project_references` 校验唯一 membership。
成片时序另由 `CompositionSpec -> resolve_composition -> ResolvedTimeline` 独占。

Agent/调用者创建 `GenerationIntent`、`ProviderNeutralGenerationIntentProjection` 和
`VideoPlanningRequest`；`VideoPlanner.plan` 唯一派生 requirement；
`require_current_video_plan -> ShotReadinessGate` 返回 verified projection；
`GenerationFeedbackOrchestrator.prepare` 消费 context loader，经
`VideoGenerationResolver.resolve_requirement` 和 adapter compiler 准备执行。
`ProductionPlanningService.prepare_generation` 只针对 selected production component 提供 facade，
并不创建 Shot intent 或 sequence edge。
`ProductionStateCommitter` 独占 Shot revision/activation 的 durable materialization。

## B. Exact Missing Seam

`VideoPlanner.derive_previous_shot_state` 已存在，但没有通用相邻 Shot materializer 调用它。
`ContinuityTransitionPolicy.create`、`CausalStateChange`、完整十项 `CausalDimension` 已存在。
`TypedStateReference` 可用 `TYPED_HASH` 绑定完整 causal column；现有 text/ref/hash 不自动提供
分维度 facts。普通 open/close prose 不能被解析成 state。
`require_feedback_context` 当前既不传 policy，也不返回 `continuity_routing`。
policy-aware `prepare_shot_for_existing_production` 存在，但 policy 是另传的 optional 参数。
实施前后的可靠 regression另确认三项 supporting阻塞：previous-base/current-target snapshots
错误相等假设；已验证v2 edge仍被legacy RouterContinuityState缺失阻断；freshness仅按asset ID/hash
索引会覆盖共享图的不同canonical owner。最小修复只改变这些证明接缝，不修改FULL能力gate。
双独立review另复现：技术PASS不证明causal close、activation pointer不能只在helper核验、
handoff stack必须重验、identity/style不应要求terminal。修复共用现有Production证据reader及QA
recipe/observations契约，不添加state/schema或第二edge owner。

## C. Existing Owner Candidates

- `VideoPlanner.derive_previous_shot_state`：previous identity/flags 的现有 constructor，必须复用。
- `ContinuityTransitionPolicy`：edge truth 与 policy hash 的现有唯一 schema，必须复用。
- `scripts/prepare_shot_continuity_p0.py`、`shot_continuity_m0_reprepare.py`：qualification-specific
  policy 工具，不是通用 authoring/sequence owner，不扩大其职责。
- `ecommerce_ad_coordinator.run_ecommerce_ad_generation`：commercial activation 顺序执行，
  不拥有通用 narrative edge 或 planning request。

## D. Historical Bypass

历史 ignored `runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/prepare.py`
在 60–67 行新建单 Shot/单 Shot Storyboard，在 126 行显式填 `previous_shot_state=None`，
129 行直接调用 Planner/readiness；150–155 行填 routing `none`、无 semantic state。
`predecessor-video` 只是普通 reference asset，没有 source Shot/accepted intent identity。
这是 task-local sequence shortcut，随后仍使用 canonical generation/committer；
不是 test-only，也不是完整 Product sequence implementation。历史 bytes 不修改。

## E. Proposed Single Owner

在 Planning 边界增加薄 `sequence_continuity` authoring adapter，读取既有 Storyboard 顺序及
canonical accepted source lifecycle，复用上述 constructors；不新增 sequence/state/continuity schema。
它产出现有 `VideoPlanningRequest`（内嵌现有 policy）、plan 和标准 production handoff。
独立 Shot 必须显式选择无 edge；相邻本身不推导 FULL。

## F. Required Inputs

exact target authored request；显式 boundary/obligation/edge semantics/take；完整既有
`CausalStateChange`；source expected identity/intent hash；current selected QA；真实 source/destination
execution stack 与 destination route；既有 anchor bindings；source accepted execution binding、
exact active video/terminal/evaluation lineage。Source close 和 target open 必须分别以现有
`TypedStateReference.TYPED_HASH` 绑定完整十维 causal column。
stack 在所选 route/profile 已知、Provider binding 之前提供，未知即 block，不造 hash。

## G. Fail Closed

FULL 缺 source、accepted lineage、intent hash、任一 causal dimension、typed column hash、
anchors、stack 或 compatible keyframe 必须停止；不得改为 standalone。
source identity/revision/hash、target request/intent、state column drift 必须停止。
reset 与 identity-only 显式声明，仍校验完整 causal changes，不默填 stable。

## H. Likely Changed Paths

Planning adapter、request 的 additive policy envelope、existing planning/readiness handoff、
feedback context/driver；对应 regression tests、matrix/baseline、bounded spec/plan。
必须先复现后才允许修正旧 route binding 对 source/target snapshot 相同的假设：
source activation 推进 Project/Registry，derived keyframe 又推进 target snapshot；
policy 应绑定 current target snapshot，source 由其 immutable execution/activation lineage证明。

## I. Explicit Non-Changes

不改 `d234233` 的 FULL conditioning gate、METASO capability、Router selection、prompt compiler、
Provider adapter、paid/credential/permit、committer/timeline/QA acceptance owners。
不改 ignored historical runs/raw FAIL，不生成真实媒体、不调用外部 API、不 push/deploy。

## Evidence Boundary

CodeGraph 已 index 并确认标准 handoff callers；当前源码/测试为事实。
RAG 有 tagged stale fragments，只作导航；AOCI whole overview host 截断，不能声称完整认知可靠。
只读 native mapper核对历史 source，Parent负责设计与最终验证。
