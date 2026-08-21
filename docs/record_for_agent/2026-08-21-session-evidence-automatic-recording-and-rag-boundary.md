# Session Evidence, Automatic Recording, And RAG Boundary Record

Date: 2026-08-21

## Purpose

本文记录 AI-VIDEO 在每个 session 结束时使用 `record-ai-video-session`，并结合
Production 自动 evidence 与 Quality Intelligence/RAG 的 operating model。目标是把
“自动事实”“会话解释”和“未来检索”连起来，但不建立第二套 Production truth。

本文是 governance/runtime boundary record，不是新的自动 evaluator、数据库、在线服务、
Provider 调用或 Final Acceptance 授权。

## The Three-Layer Model

### 1. Automatic Production Evidence

生成 Shot 后，P8 lifecycle 自动持久化 request、submit/poll、fetch、measured probe、
provenance、candidate 与 Manifest activation evidence。MP4 bytes 和 receipts 使用
content-addressed identity；`ProductionStateCommitter` 继续独占 candidate、activation
与 recovery。

Continuity-bound Shot 还必须有 policy-selected reviewer/evaluator 提交的
`GeneratedShotContinuityEvidence`。该 evidence 绑定 exact Shot、request、MP4、
constraints、QA policy 与 evaluator identity，最终 PASS/FAIL/NOT_EVALUATED 由 P6
adjudicator 派生。当前没有通用自动视觉 evaluator；缺 evaluator 时 fail closed。

### 2. End-Of-Session Durable Record

每个稳定 session 结束时调用 `record-ai-video-session` 是合适的 handoff protocol。它
记录的是：

- 本轮做了什么、为什么做；
- 使用的 commit、tests、Harness receipt、artifact path/hash；
- technical acceptance、human/subjective acceptance、live/paid 与 replay 的边界；
- 未完成、未知 outcome、dirty ownership 与下一步。

它不应复制完整 JSONL、raw Provider response 或全部自动 receipts，而应引用 canonical
paths，并把决策、解释和 remaining risk 变成 future Agent 可读的 durable context。

### 3. Quality Intelligence And RAG

`QualityExperienceRecordV1` 是独立的 Q0 passive-capture 数据面。它可以把 exact attempt、
artifact、measurements、human verdict、intervention 和 controls 绑定到显式 dataset root，
再由 exact lookup 或 sanitized advisory projection 提供 RAG context。

当前 Q0 没有自动挂到每次 P8 Shot 生成之后；必须显式 capture。RAG projection 只能提供
advisory experience，不能写 Manifest、Registry、Planner、Router、Provider state，也不能
替代 P6 semantic PASS 或 Final Acceptance。

## Assessment

这三层组合已经形成接近完整的闭环，但不是“完美自动化”：

`Production receipts = 当前事实`，`session record = 人类可读的决策/交接解释`，
`Q0/RAG = 可追溯的历史经验检索`。

任何一层都不能单独替代另外两层：

- session record 不能证明 runtime 已实现；
- receipt 不能解释为什么选择某个 repair 或判断某个 Shot 是否好看；
- RAG 不能因为历史案例相似就自动选 Provider、自动 activation 或自动 Final Acceptance。

## Recommended Session-Close Protocol

在 session 达到稳定 checkpoint 后：

1. 先确认代码、Manifest、artifact、tests 和 Git state 的 current truth；
2. 让 Production/Q0 自动或显式写入可验证的 content-addressed evidence；
3. 调用 `record-ai-video-session`，只引用已验证 evidence 并写清 unresolved boundary；
4. 未来 Agent 通过 exact lookup/RAG 读取 advisory context，再回到 source code、receipts
   和 current runtime 验证，不把 record/RAG 当成更高 authority。

该流程可以作为 session close checklist，但目前不存在强制自动 hook；如果用户忘记调用
skill，不应假设 record 已存在。

## Guardrails

- Product Runtime 不得 import、执行或依赖 `record-ai-video-session`、`.agent/`、`.agents/`
  或 Agent Memory；这些属于 Development Governance。
- 自动 record 必须由 canonical owner 产生，不能由 RAG 或 session prose 伪造。
- RAG 只读、可解释、带 provenance/freshness；历史记录与 current code/tests 冲突时以
  current executable truth 为准。
- Quality experience 不能把 technical PASS、Provider success、fetch completion 或
  playback success 外推成 subjective quality acceptance。
- Unknown outcome、缺 reviewer、stale evidence 或不完整 continuity coverage 必须保持
  fail closed，不得由 session record 或 RAG 自动补齐。
- 当前 workspace 另有并行 dirty/staged changes；本 record 不包含、不 stage、不 commit
  其他 files。

## Remaining Work

- 为每次生成 Shot 建立可选但明确授权的 Q0 capture hook，仍保持 dataset-root-only 和
  Production writer ownership；这需要单独 implementation scope，不由本记录批准。
- 实现 hybrid continuity evaluator 后，再把其 raw evidence 接入现有 P6 seam；不要让
  evaluator 自报 verdict。
- 如需自动 session-close hook、自动 Q0 capture、远程 vision backend、credential 或
  budget/egress，需要独立 contract/spec 与用户授权。
