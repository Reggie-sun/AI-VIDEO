# Post-QA Q0 Automatic Caller — When To Implement

## Status

Deferred until the Q0 post-QA capture foundation is merged into `main` and a product-level
application orchestration owner is explicitly accepted。

当前不应直接把 automatic capture 接入 `VideoGenerationService`、`ProductionStateCommitter`、
continuity evaluator/reviewer callback、P6 receipt writer 或 Provider lifecycle。Q0 capture API
完成并通过验证，只表示 capture seam 可被显式调用；不表示产品已经接受“每个 Shot 自动调用”的
orchestration owner。

## When The Next Step Can Start

### Current Answer — 2026-08-22

**现在还不能开始 automatic-caller implementation。** 当前 `main` 尚未包含 Q0 post-QA capture
foundation commit `509acc6760c364247515db567432fe6ca9c8a03d`；因此下一步仍是先完成该 commit 的安全
integration，并在合并后的 exact tree 上重新验证。

**automatic-caller spec + plan 可以在以下事件全部发生后立即开始：**

1. Q0 capture foundation 已进入当前 `main`；
2. 合并时与当前 `main` 的 same-file edits 已由各自 owner 明确 reconciliation，没有覆盖并发工作；
3. 合并结果的 focused tests、Architecture Gate 与 Harness receipt 为 fresh/passing；
4. `main` 上的 executable truth 仍保持 Production 不 import Q0、显式 capture replay/zero-write contract
   通过。

满足这四项后，不需要等待 live Provider、媒体生成、paid smoke、RAG rebuild 或真实 Pilot 数据，便可以
开始下一步 spec + plan。

**automatic-caller implementation 只能在 spec + plan 又满足以下条件后开始：**

1. spec 状态为 `Accepted`，plan 明确引用该 spec；
2. application-level orchestration owner 已落实到精确 module/API，而不是抽象地写“未来 Product
   Agent Loop”；
3. Q0 pilot/run context 的 canonical source 已接受，caller 无需猜测或伪造 context；
4. trigger 明确位于 durable post-QA checkpoint 之后；
5. complete analyzer evidence 的来源和 exact artifact binding 已确定；
6. failure isolation、replay、conflict、privacy 与 offline E2E acceptance tests 已写清；
7. implementation target files 没有 active same-file writer conflict。

因此实际顺序固定为：

```text
Q0 capture foundation merge to main
  -> merged-tree verification and fresh receipt
  -> automatic-caller spec + plan
  -> owner/context/trigger contracts accepted
  -> strict RED/GREEN implementation
```

## Goal

在 Production QA checkpoint 已经完成后，由唯一 application-level caller 自动调用
`capture_post_qa_quality_experience()`，将 exact continuity-bound generated-video attempt 投影为
`QualityExperienceRecordV1`，同时保持：

- Production lifecycle 不依赖 Q0；
- Q0 capture failure 不阻断、不回滚已完成的 Production lifecycle；
- caller 不伪造 experiment、review、analyzer 或 runtime evidence；
- replay 不重复 Provider、probe、evaluator、analyzer、recovery、activation 或 Manifest write。

## Relationship To The Continuity Review Coordinator

`docs/when_to_do/2026-08-22-continuity-review-coordinator-and-human-evidence-ui.md` 描述的是
continuity evaluator 与 exact-bound human decision 的产品调用路径。它负责形成或重开 durable
continuity/P6 evidence，不负责写 Q0 dataset。

未来 Q0 automatic caller 位于其后：

```text
generated-video attempt
  -> continuity review/evaluator
  -> P6-derived PASS or FAIL
  -> durable QA checkpoint complete
  -> application-level Q0 automatic caller
  -> capture_post_qa_quality_experience()
  -> QualityExperienceStore.write_record()
```

两者不得合并成一个 Production writer，也不得让 continuity coordinator import
`ai_video.quality_intelligence`。

## Implement Only When

必须同时满足以下条件，才开始 automatic-caller implementation：

1. Q0 post-QA capture foundation 已经进入当前 `main`，且 exact commit/range Harness 仍有效；
2. 已接受一个位于 Production 与 Q0 之上的 application-level orchestration owner；
3. 该 owner 能获得显式、不可伪造的 Pilot/Q0 capture context；
4. exact attempt 已有 durable continuity evaluator evidence，并可由 pure P6 adjudicator 派生
   `PASS` 或 `FAIL`；
5. complete canonical analyzer measurement evidence 已存在并与 exact MP4 绑定；
6. caller 的 failure isolation、replay、conflict 与 observability contract 已写入 spec/tests；
7. 当前 `main` 没有 same-file ownership conflict，且 implementation 使用独立 task snapshot。

任一条件不满足时，继续使用显式 post-QA capture API，不实现 automatic invocation。

## Required Owner Decision

实现前必须接受一个明确 owner。该 owner 应是 application-level one-shot coordinator，而不是：

- 新的 Manifest/Registry/P6 writer；
- `ProductionStateCommitter` mixin；
- evaluator/reviewer callback；
- Provider adapter 或 fetch/activation service；
- background directory watcher、daemon 或 queue；
- 未被接受的通用 Product Agent Loop。

owner 可以调用 Production 的 strict read seam 和 Q0 capture API，但 Product Runtime 不得反向依赖
`ai_video.quality_intelligence`。若仓库尚无合适 application module，引入新 subsystem 属于独立
Decision Gate，必须先通过 spec 接受，不能借 automatic caller 顺带创建。

## Q0 Context Contract

automatic caller 不得自行生成或从 Production runtime 猜测以下字段：

- experiment/pilot identity；
- repository commit；
- purpose/hypothesis；
- capture actor 与 authorization boundary；
- attempt kind/predecessor；
- analyzer measurement sources；
- Q0 human-review metadata；
- interventions、controls 与 confounders。

这些信息必须由上游 pilot/run envelope 或其他 accepted application context owner 显式提供，并在调用
前冻结。Production evidence 继续由 capture API strict-reopen，caller 不得提交已经拼好的
`QualityExperienceRecordV1`。

## Initial Automatic Scope

第一版只覆盖：

- continuity-bound generated-video attempt；
- durable evaluator state 为 `EVIDENCED`；
- pure adjudication 结果为 `PASS` 或 `FAIL`；
- exact artifact/probe/provenance/profile/policy/constraints/Shot binding 完整；
- complete analyzer evidence；
- explicit Q0 context 完整；
- same identity replay 与 typed conflict；
- capture error 被隔离并记录，但不改变 Production lifecycle。

## Keep Deferred

以下仍不属于第一版 automatic caller：

- `NOT_EVALUATED` 或缺失 human fallback；
- evaluator intent-only、missing/tampered/stale evidence；
- Provider failure 或 Provider outcome-unknown；
- non-continuity Shot；
- 自动运行 analyzer、probe、evaluator、recovery 或 P6；
- 自动创建 Pilot dataset index、cohort 或 roster；
- background retry、daemon、queue manager 或通用 terminal-attempt orchestration；
- live Provider、媒体生成、paid/remote call 或 Agent Memory/RAG rebuild。

## Acceptance Criteria

- automatic caller 有唯一 accepted application-level owner；
- Production package 不 import Q0；
- trigger 只发生在 durable post-QA checkpoint 之后；
- caller 不能覆盖 runtime truth，也不能伪造 Q0 context；
- `PASS`/`FAIL` mapping 与显式 capture API 完全一致；
- `NOT_EVALUATED`、missing、stale 或 tampered evidence fail closed 且 Q0 zero-write；
- exact replay zero-side-effect，conflict typed；
- capture failure 不阻断或回滚 Production lifecycle；
- focused E2E 使用 offline fixture，不运行 live Provider、媒体或网络。

## Recommended Next Step

先完成 Q0 post-QA capture commit 到 `main` 的安全 integration。随后创建独立 spec + plan，先接受：

1. application-level owner；
2. Q0 context source；
3. exact trigger point；
4. failure isolation 与 replay contract。

上述四项稳定后，再开始 strict RED/GREEN implementation。不要在当前 capture foundation commit 或
continuity reviewer callback 中顺带实现。
