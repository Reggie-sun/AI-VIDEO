# Current Shot Close Expression Spec

## Goal And Scope

fresh Shot 在 generation 前声明完整 hash-bound current close，compiler 与 evaluator 消费同一 authored truth。
修复 local H3 hash-as-text。全部验证离线，真实媒体 quality 不在本次 acceptance 内。

## Authoring Contract

Case C：在现有 `GenerationIntent` 增加 optional `close_causal_facts`，key 复用唯一 `CausalDimension`，
value 是明确、非空、NFC semantic text。author 必须逐维声明，不能由 compiler 从 endpoint/performance 推测。
缺字段、重复维度、unresolved 或 hash mismatch 拒绝。字段缺省不序列化，以保持历史 hashes/goldens。
`TypedStateReference` 不变：text/ref/hash 仍严格互斥。
complete facts 按 dimension.value 排序，canonical SHA-256 与 `close_state.state_hash` 精确一致。
不新增第二 GenerationIntent、NarrativeState、StateContract、transition policy 或 dimension enum。

## Expression Ownership

existing GenerationIntent 是唯一 current-close semantic owner；封存 requirement 已携 preimage，
因此无需机械添加 `VerifiedCausalClosingExpression`。shared leaf owner 重验 requirement、完整 facts、
close hash、provider-bound requirement hash 和 exact target Shot，才返回 `closing_facts`。
opening 仍只调用 existing sequence-issued `opening_facts`，无双向复用。
endpoint API 与 deterministic renderer 可以共享；remote/local 完整 grammar 不合并。
arbitrary current hash 缺 preimage → `PROMPT_EXPRESSION_UNSUPPORTED` / `H3PromptUnsupported`。
opening evidence 不授权 closing，包括同 digest。

## QA Contract

current close acceptance 必须是 selected QA raw-generation analyzer/human exact rule，
`intent_paths == (generation_intent.close_state.state_hash,)` 且 observable 等于 close seal。
evaluation question 从 immutable execution projection 的 requirement 重开 complete preimage，
派生完整 close facts 与 exact hash criterion；item hash 同时绑定 rubric/request/media 与派生 question。
presentation、source-to-findings projection、experience/diagnosis reopen 重新派生相同问题，
不从 prompt 推导 truth，不信任 evaluator 自带 preimage。新 facts 不接受只见 hash 的旧问题作为 PASS。
旧不带该字段的 historical evidence 保留原语义，不改 old FAIL/NOT_EVALUATED。
fresh source 需要 existing marked QA / controlled analyzer presentation，human integration 缺失保持阻断。

## Integration And Compatibility

复用 Planner → Readiness → Router → selected compiler → exact pre-submit，selection/authority 不变。
local consumers 共用 shared endpoint seam；unsupported 不降级 legacy prompt。
compiler boundary 重编 exact native grammar，防止 forged hash control-path coverage。
无facts历史 TYPED_TEXT goldens、public lifecycle/Manifest schema/StateCommitter ownership 不变。

## Acceptance And Verification

覆盖 remote opening regression/arbitrary hash、complete close、missing/mismatch/wrong target/stale、
opening≠closing authority/equal digest、text goldens、local hash rejection/verified expression。
provider-neutral fresh fixture无 previous edge，经真实 Planner/Router/native/pre-submit，0 effects。
QA question 和 source reopen经 scripted media/evaluation证明 wiring；负向覆盖 hash-only/stale evaluation。
project-native focused suites + exact owned commit-range Harness；未覆盖真实媒体保持 NOT_EVALUATED。

## Non-goals

不编辑 S02/S03、历史 evidence、Router selection、METASO capability、paid gates、Manifest schema。
不 credential lookup、submit、consume permit、generate video、fallback 或自动 author close facts。

## Self Review

授权来自当前 bounded implementation 请求；research证明需要 additive authoring field。
单一 canonical owner、独立 endpoints、fail-closed 与 unchanged historical serialization 均有验证 seam。
本 Spec 不授予新的 live effect 或真实 media acceptance。
