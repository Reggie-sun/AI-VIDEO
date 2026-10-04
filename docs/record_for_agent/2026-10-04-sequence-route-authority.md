---
record_kind: architecture_implementation
topic_id: sequence-destination-route-authority
learning_eligibility: ineligible
---

# Sequence Destination Route Authority Record

Date: 2026-10-04
Updated: 2026-10-05

## Purpose And Research Baseline

审查起点为 `main` 的 `fc72e35c2fc43a059b8b77e22635dc2fc262670e`，包含
`e733d468b86e` sequence materialization 与 `d234233948b2` FULL capability gate。
本记录保存已通过 native verification 的研究/实现 checkpoint；最终 Harness、independent review
与 publication 各自仍需 exact snapshot evidence，不以本记录或测试数量代替。

## Research Result

1. **Current exact ownership chain:** `VideoPlanner.plan` →
   `require_current_video_plan` / `ShotReadinessGate` → verified provider-neutral requirement →
   `GenerationFeedbackOrchestrator.prepare` → `create_generation_candidates` →
   `VideoGenerationResolver.resolve_requirement` → `resolve_generation_decision` → selected
   `ProviderBoundVideoRequest` → selected Provider `compile_request` / `resolve` →
   `GenerationDecisionExecutionBinding.create`。binding 重新执行 canonical decision，核对 compiled
   Provider/model/profile/capability/compiler。Router 同时拥有 selection 与 compatibility validation。
2. **Who creates destination_route today:** 原 HEAD 中 sequence caller 必须提供它；builder 只从
   accepted source bound request 创建 source route。仓库内所有 sequence caller 都是 tests，
   `_edge_inputs` 传同一个 source route；fixture 的 `_bound_route_identity` 调用
   `ProviderRouteIdentity.create`。该 constructor 只校验自计算内容 hash，不签发 selection authority。
3. **Who creates destination_execution_stack today:** 原 sequence fixture 用
   `_execution_stack_identity` 手工创建，再将已接受 source 的 exact stack 同时作为 destination。
   `GenerationExecutionStackIdentity.create/materialize` 只绑定 profile/compiler/workflow/components
   身份；`shot_continuity_source_stack`、qualification committer 与 task-local preparation script
   是现有具体 materialization 路径，不是通用 destination selector。
   `lifecycle` 由 caller/context loader 提供 generation/output IDs、当前 Manifest pointers、frame
   binding 与 stack hash；fixture `_edge_inputs` 手工构造。它不是 Provider selection receipt，
   最终仍由 current-project / routing / execution seam 核验。
4. **Sequence adapter selection verdict:** same-stack 是继承已接受 authority；原 cross-stack API
   则会把 caller 选择的 exact Provider/profile/capability 封成 immutable 排他约束，缺少 canonical
   selection evidence。无通用 production caller，不能宣称发生过真实 Provider 副作用。
5. **Same-stack verdict:** continuous take 的 policy 强制两端 stack hash 相等；route binding 强制
   same-stack route equality；accepted source reopening 核对实际 compiled request stack hash。
   因此 `destination_route = source_route` 唯一确定，same-stack HARD_CUT/FULL 也成立。
6. **Cross-stack verdict:** HARD_CUT/FULL 允许不同 stack；原 binding 只核对 route/stack 的字段与
   hash，不能证明 B 经 canonical selection。不是“仅参数”的问题，而是候选会因该参数被排除。
7. **Circular dependency:** 原新 destination 有循环：exact route/stack → policy → neutral requirement
   → Router selection。same-stack 用已接受 source 打破循环。现有 `GenerationDecisionExecutionBinding`
   可以表达先前 neutral-seed selection；无需第二 proposal/policy schema。
8. **Architecture classification:** **Case C，exported API authority boundary**。现有 tests 的
   same-stack 安全范围不足以使 unrestricted cross-stack API 自动安全；没有 live effect 的证据。
9. **Blocking issue:** caller-created route 经 `ContinuityProviderRouteBinding` 封存后，
   `_video_requirement_routing.apply_continuity_transition` 用 destination equality 过滤候选；Router
   会验证被提前选定的 B，而不是从原合法候选集合保持独立选择。
10. **Minimal fix boundary:** source inheritance 与 cross-stack prior-selection evidence admission /
    reopen；不改 Planner derivation、candidate ranking、registry、Provider capability/prompt 或 committer。

## Exact Code Evidence

| Concern | Current code owner / call path |
| --- | --- |
| Operator registration | `production/generation_feedback.py::RegisteredGenerationTarget` 提供已注册 profile/compiler/output；不是 fit selector |
| Actual candidate enumeration | `generation_feedback.py::create_generation_candidates` 遍历 `provider.capabilities().variants`；不排名 |
| Exact provider lookup | `production/video.py::VideoProviderRegistry.resolve`；无 selection/fallback |
| Selection and binding | `shot_router.py::VideoGenerationResolver.resolve_requirement` → `generation_decision.py::resolve_generation_decision`；先全候选 `_bind_requirement` assessment，再 `fit_rank`、tie rejection、chosen binding |
| Compilation ordering | `GenerationFeedbackOrchestrator.prepare` 只在 `GENERATE_ONCE` 后编译 selected candidate |
| Execution authority replay | `generation_execution.py::GenerationDecisionExecutionBinding._validate_binding` 重算 decision；`validate_current_project` 重验 canonical target/snapshots/assets |
| Stack identity | `video_execution_stack.py::GenerationExecutionStackIdentity.create/materialize` 与 `ExecutionStackMaterialization`；content identity 不等于 selection |
| Same-stack invariant | `video_transition.py::ContinuityTransitionPolicy._validate_policy` 的 continuous-take equality；`_shot_router_contracts.py::ContinuityProviderRouteBinding._validate_binding` 的 route/stack equality |
| Preselected route exclusion | `_video_requirement_routing.py::apply_continuity_transition` 的 `CONTINUITY_PROVIDER_LOCKED` / `CONTINUITY_DESTINATION_ROUTE_MISMATCH` |
| Canonical new execution reopen | `production/_sequence_source.py::require_sequence_source`；public resolver、feedback context、execution binding 共用 |
| Sequence wrapper callers | `planning/sequence_continuity.py::prepare_sequence_shot_for_existing_production` → builder → Planner → Readiness → callback；仓库内只有 `tests/test_planning_sequence_continuity.py` 驱动 |

原 HEAD 的 public Router 离线复现提供两个合法候选 A/B，再由 caller 封入 B。
结果为 `GENERATE_ONCE / B`，A 唯一 route blocker 是
`CONTINUITY_DESTINATION_ROUTE_MISMATCH`。另一复现可在无 destination-selection receipt 时把
手工 route/stack 封入 policy。两者均使用 fake fixtures，无真实 Provider/credential/media。
这是可执行的 ownership 证据，不由文档措辞或模型意见推出。

## Implemented Authority Boundary

same-stack 可省略 destination route/stack，由 accepted source execution binding 推导；显式不同
route 被拒绝。source stack 仍必须与 accepted request hash 匹配，lifecycle 仍绑定 exact destination。

cross-stack 必须带 existing `GenerationDecisionExecutionBinding`。其 owner 新增只读
`selected_provider_route` 与 `require_sequence_destination_selection`，重新反序列化、重算 decision，
核对 exact target/intent/current snapshots/lifecycle/compiled stack/route。adapter 还核对 prior binding
使用 exact unmaterialized seed 的 Planner-derived projection。prior binding 不得携带 continuity route，
禁止用被 sequence 排他约束选出的最终 decision 反过来证明初始 authority。

既有 `ContinuityProviderRouteBinding` additive 保存该 existing type 的 canonical JSON，避免
循环 model import；不是新的 schema、receipt 或 Router。None 省略，保留旧 binding bytes/hash。
`require_sequence_source` 在新 Production preparation / public resolution / execution reopen 时
再次强制 cross-stack evidence，并以同一既有 authoring-seal payload 核验 prior selection 的 neutral
seed hash；历史纯解析与 compatibility prediction 不签发新 execution 权。

合法的 cross-stack 顺序为：neutral seed Planner/Readiness → existing canonical Router selection /
compiled binding → sequence policy materialization → sequence-aware Planner/Readiness → existing
Router final selection/validation → native compilation。先前 binding 不能执行最终 requirement。
最终 Router 可拒绝 mismatch 或 FULL/C2 incompatibility，不能静默替换 immutable destination。
这复用已有 binding checkpoint，不新增 preselection orchestrator；缺 proof 就 STOP。

cross-stack binding 另保存已有 materialized `VideoPlanningRequest` 的 canonical JSON preimage。
共享 reopen 以其内容 hash 对照实际 final requirement 的 `source_request_content_hash`，核对内嵌
policy，然后从相同 preimage 移除 sequence policy、恢复 `previous_shot_state=None`，核验 prior
neutral seed hash 和 authoring seal。这里只验证既有数据身份，不推导 Planner requirement、引入
Production → Planning import 或第二 schema。same-stack omission 保持历史 binding hash。

## Independent Review Reproduction And Consolidation

第一 candidate `76790a84163a523e11f4e62da59b0221ca4cd82a` 的 16 项 exact commit-range Harness
checks 已通过；两个同快照独立 native reviewer 分别给出 `SA-001` / `SAR-001`：builder/feedback
核验 exact neutral seed，但 public Resolver/execution 的共享 reopen 缺少同一 authoring-seal 关联。
Parent 没有以 verdict 代替验证，而是从改变 `production_policy.accept_static_image_fallback` 的
另一合法 seed 正常取得 canonical selection，替换 proof 并重新封存 routing/execution binding。
RED 为 **2 failed（Resolver/execution）、1 passed（feedback）**，确认入口差异。

最小修复将既有 authoring-seal hash 计算归并到 `_sequence_source`；所有 cross-stack reopen
以 source binding、accepted media、当前 Storyboard、causal changes 和 prior seed hash 重算 seal。
builder/feedback 复用相同 payload；没有新增 schema、selector、receipt 或 planning request 字段。
同一替换回归 GREEN 为 **3 passed**。第一轮 receipt/review 只保留为历史，不能替代修复快照的新
Harness 与双独立复审。具体 Parent 裁决保存在 run `001` 的 `final-review-round1.json`。

第二 candidate `ac9dfa5a0fef6aea6360d8ea2eb5969df746966d` 的 16 项 checks 与 freshness 也通过，
但 round 2 review 仍发现 `SA-001` / `SAR-001` 未关闭：完整合法 other-seed policy+binding 与原
final projection 配对时，内部 seal 一致但不能证明实际 final planning lineage。Parent 从正常
builder 生成完整替换 package，在 public Resolver/resealed execution 复现 **2 failed**。
将同一场景纳入 repository test 后为 **2 failed、feedback 1 passed**；feedback 原有 exact-policy
检查已经阻断，不把测试的错误消息匹配差异当作新的 runtime bug。

上述 request-preimage 最小补强直接关联 final request/policy/prior seed；九项核心 GREEN 包括
完整替换、单 selection 替换、缺 preimage 和合法 cross-stack 对照。run `002` 保存 Parent RED、
双审与历史 receipt；passing Harness 不代替 blocking review finding。最终新 snapshot 仍须独立
核验 run `003` 与 round 3 review，不以旧 passing receipts 代替。

## Verification And Evidence

- RED：原实现 same-stack omission 两项失败，bare cross-stack route 到达被禁止的 Planner，三项
  regression 先证实失败，再修复。
- Final native sequence suite：`tests/test_planning_sequence_continuity.py`，**51 passed**；覆盖继承、
  same-stack forgery、有效 cross-stack prior selection、最终 route/stack 一致、bare route、stale
  route/stack/lifecycle/seed/target、tampered decision、candidate tie、circular proof、legacy bypass，
  以及单 selection / 完整合法 policy+binding 替换和缺 planning request preimage 在
  feedback/public Resolver/resealed execution 的拒绝行为。
- 其他相关 native suites：Planner、Router、transition、Readiness、feedback、execution/guards、
  generation decision，**395 passed**。包括 METASO soft Ref2VA FULL gate、HardCutKeyframe C2、
  identity/style carryover 与 reset；没有修改这些媒体/capability contracts。
- Task Architecture Gate：PASS；`_shot_router_contracts.py` 有既有 oversized-module growth WARN，
  effective LOC `951 → 957`。增加的是既有 cohesive binding 的 evidence 字段/None serialization，
  admission/reopen logic 位于既有 execution owner；未刷新 debt baseline 或清理 unrelated code。
- `git diff --check`：PASS。最终 exact Harness 与两个独立 T3 review 的 evidence 存于
  `.agent/harness/runs/sequence-route-authority-20261004-003/`；须分别核验 snapshot、policy、artifact
  与 freshness，不能从本记录或 native tests 推定它们通过。

## Remaining Evidence Boundaries

当前仍没有 generic production sequence orchestration driver；tests 的 callback 不是已交付产品集成。
本轮没有真实 Provider 请求、credential lookup、视频生成、QA/P6/Final Acceptance mutation 或
历史 media verdict 变更。源/目标编译与临时 project 的 fake acceptance 是离线测试。

AOCI `aoci_maintain` 返回 `stopped / blocked`，没有发放可写 candidate；最新有 42 条 observed-scope
review 与 5 个 stale owner 阻挡 whole-index alignment，包括 task-owned matrix/baseline/execution
与 unrelated `AGENTS.md` / Harness policy。当前 Guide 要求全 scope review；不虚假 acknowledge
未审查的 unrelated 历史，也不修改其正式资产。结论依靠当前源码、CodeGraph 与 executable tests，
不声称 AOCI complete cognition 或索引已对齐。

## Learning Evaluation

`distill-ai-video-learning`：`no_candidate`。本记录是单次 engineering architecture checkpoint，
`learning_eligibility: ineligible`；没有可支持新的跨实验媒体/Provider claim 的独立 attempts 或
controlled multi-arm evidence，也未改既有 pending/adopted Learning Claim。
