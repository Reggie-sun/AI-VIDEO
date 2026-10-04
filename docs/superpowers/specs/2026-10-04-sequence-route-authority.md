# Sequence Destination Route Authority

## Scope And Root Cause

研究基线 `fc72e35c2fc43a059b8b77e22635dc2fc262670e`。sequence API 的仓库内 caller
只有 same-stack tests，但 public API 可把 caller-created cross-stack route 封成排他约束。
离线 HARD_CUT/FULL 复现：两个合法候选 A/B，caller 封入 B，public Router 返回
`GENERATE_ONCE / B`，A 的唯一阻断理由为 `CONTINUITY_DESTINATION_ROUTE_MISMATCH`。
content hash 与 materialization 不证明 selection authority，分类为 Case C（API 边界）。

## Canonical Authority

`RegisteredGenerationTarget` 是 operator registration；`create_generation_candidates` 枚举
实际 variants。`VideoGenerationResolver.resolve_requirement` / `resolve_generation_decision`
独占 candidate compatibility、fit ranking 和 selection。`GenerationDecisionExecutionBinding`
重算该 decision、绑定编译结果；stack materializer 只证明 execution identity，不选择 Provider。

same-stack 从 accepted source binding 推导 route；caller destination 参数仅是 exact assertion。
cross-stack 必须提供 existing `GenerationDecisionExecutionBinding`，其 selection 已经经过
自己的 provider-neutral Planner/Readiness 与 canonical Router，不能用裸 route 或 candidate 替代。
此 evidence 绑定当前未 materialized 的 target planning seed、canonical Shot/intent、snapshots、
lifecycle、exact stack 与 selected route，且不得自身携带 continuity route 预选约束。
缺 evidence 时停止，不新增 preselection orchestrator 或自动生成该 evidence。

先前 decision 和最终 sequence-aware decision 是两个不同 checkpoint：先前 binding 不授予
新 requirement 的执行权；完整 sequence policy 经 Planner/Readiness 后仍须由 Router 选择、
校验 FULL/C2 和 exact destination。最终 decision 可拒绝，不能静默替换封存 route。

## Evidence And Compatibility

在既有 `ContinuityProviderRouteBinding` 中 additive 保存 existing execution binding 的 canonical
JSON representation；不是第二 schema/receipt。缺字段保持旧 bytes/hash。新 cross-stack preparation
和 execution 必须重新反序列化既有 type、重算 selection、核验当前 project。历史 pure parsing 与
compatibility prediction 不因此变成 new execution authority。
所有 cross-stack Production reopen 还须以既有 authoring seal 核验 prior selection 的 exact seed
hash；builder、feedback 与共享 reopen 使用同一 seal payload，合法但来自另一 seed 的 binding
不能成为当前 policy 的 authority。无需新增 seed/route schema。
既有 route binding 同时保存 materialized `VideoPlanningRequest` 的 canonical JSON preimage。
共享 reopen 校验其内容 hash 等于实际 final requirement 的 `source_request_content_hash`、内嵌
policy 等于当前 routing policy，再从同一 preimage 去掉 sequence fields，核验 prior neutral seed。
此 evidence 只绑定既有类型的字节身份，不新增 Planner derivation。
完整合法 policy+selection 来自另一 request 时，也不能授权当前 final requirement。
same-stack old bindings 无需此新增 evidence，route equality 与 source activation proof 继续强制。

hash 一致不证明 prior projection 是该 seed 的 Planner 输出。共享 reopen 必须重新创建 exact
neutral `VideoPlanningRequest`，调用既有 `VideoPlanner.plan` / `require_current_video_plan`，比较
完整 verified projection。采用 `ARCH103` 的唯一 exact source/target read-only exception：
`production/_sequence_source.py` → `planning.video_planner`，仅用于纯 derivation/readiness 验证，
不调用 handoff、selection、Provider 或其他 effect；review-by 为 `2026-11-05`。
其他 Production → Planning / QA / Q0 依赖仍阻断，不新增 callback registration、私有 proof cache
或复制 Planner 规则。该任务内 contract amendment 由 Parent self-review；canonical derivation
owner 保持 Planning，增强真实 admission，而非将 caller 的自洽 hash 当作 authority。

## Acceptance And Non-Goals

覆盖用户十项 tests：same-stack inheritance/forgery；cross-stack canonical selection 与任意 route
拒绝；Router mismatch；final stack equality；neutral Planner；METASO FULL、C2、carryover/reset。
补充 stale/tampered/circular selection evidence 与 Production reopen 的否定路径，包括合法的
other-seed binding 单独替换、完整合法 policy+binding 替换，以及缺 request preimage 后，public
Resolver 与完全重新封存的 execution binding 的拒绝行为。
另覆盖 same-seed/hash 的自洽伪造 prior projection，在 builder/feedback/public Resolver/resealed
execution 四个入口均拒绝；exact dependency exception 不扩大到其他 path 或 QA target。
不改 Planner derivation、generation ranking、registry、Provider capability/prompt、paid/credential、
committer、media/verdict/timeline，不调用 Provider、不读取 secret、不生成真实媒体。

## Verification And Self Review

先 RED，再 targeted Planner/Readiness/Router/feedback/execution suites、Architecture Gate 与 exact
staged snapshot 或 exact commit range Harness。T3 ownership boundary 在同一 stable snapshot 双独立 read-only native final review；
当前 no Provider/credential 指令优先于 standing Kimi route。Parent 裁决 findings。
Self-review：仅复用已有 execution binding，初始 selection 不消费 caller route；最终 FULL 仍独立
验证；旧 evidence 不改写，new execution boundary fail closed。无需新 policy 或 semantic phase schema。
