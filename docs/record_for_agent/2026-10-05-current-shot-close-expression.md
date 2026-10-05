---
record_kind: architecture_implementation
topic_id: current-shot-close-semantic-expression
learning_eligibility: ineligible
---

# Current Shot Close Expression Record

Date: 2026-10-05

## Purpose And Baseline

解决source-bootstrap authoring/preimage缺口与local H3 hash-as-text。初始fetch确认
`HEAD == origin/main == d607726643a25bcbaadd3debaa0ec7ef36337201`。
同工作区existing staged Harness granularity任务未纳入本任务、未改写或清理。

## Architecture Decision

Case C：局部终态字段不能确定十维close truth；previous-close → current-open policy亦不拥有current close。
新增existing `GenerationIntent.close_causal_facts`，复用唯一enum；TypedStateReference仍hash/text/ref互斥。
current close的author提供全部facts；canonical SHA与close_state精确一致。
无需新增closing expression class，因为immutable requirement已携authoritative preimage。
opening沿用ephemeral sequence-issued evidence，独立closing投影不消费opening authority。
详细owner/path见[research](../research/2026-10-05-current-shot-close-expression.md)、
[spec](../superpowers/specs/2026-10-05-current-shot-close-expression.md)、
[plan](../superpowers/plans/2026-10-05-current-shot-close-expression.md)。

## Current Runtime Truth

remote/local native grammar共用endpoint验证与fact renderer；不共享整个prompt grammar。
local H3、T8 Quality/Turbo/Native/Long不再使用state_hash作为semantic prose；无verified preimage拒绝。
complete close在exact requirement/Shot/bound request重验后表达，不能用opening授权closing，等digest仍拒绝。
compiler重编claimed hash coverage，persisted recipe与QA seal保留；只从verified临时lexical view移除digest。
QA selected raw semantic rule仍引用exact close hash；controlled question从同一execution requirement
派生complete facts并绑定requirement/Shot/request/media。source/experience/diagnosis重开同一问题。

## Verification And Evidence

Red tests复现authoring字段缺失及local任意hash仍compiled。focused text/local adapter/evaluator suites：203 PASS。
existing remote opening regressions：26 PASS。local selected T8 Native I2VA新增hash-bound close compile：2 PASS。
fresh no-previous-edge fixture经Planner/Router/selected METASO compiler/exact pre-submit保持REQUEST、0真实effects。
offline scripted backend提供fixture MP4；controlled analyzer收到完整facts，scripted PASS经existing
committer记录，随后validate/activate/terminal extraction，accepted_sequence_source(require_causal_close=True)重开成功。
新QA负例覆盖hash-only、stale、missing与wrong Shot问题；它们不是实际媒体观察。
exact最终snapshot的Harness scope/result由`.agent/harness/runs/`内receipt独占，最终交付引用实际receipt。

## Review And Tool Boundaries

read-only native code_mapper独立追踪QA hash-only缺口。当前禁止credential lookup和外部Provider效果优先于
Kimi standing route（该route必须live credential injection），所以没有Kimi调用或route proof。
所有effects限tests临时目录/scripted transport；未读取credential、消耗真实paid permit或生成真实Provider视频。
Agent Memory检索exit 3，按Skill未重试/前台重建；AOCI维护返回`stopped/blocked`，
existing managed scope包含非本任务stale/pending对象且未发可写candidate；未越界治理，索引仍不aligned。
record-ai-video-session主动评估为record；distill-ai-video-learning评估为no_candidate：
本次是一个implementation/fixture链，缺少独立真实实验，不创建learning/adoption artifact。

## Remaining Boundary

source-bootstrap的软件契约与离线闭环已具备；真实fresh Shot仍须explicit authoring、current selected QA、
actual exact-media analyzer/human verdict与existing activation/terminal proof。human presentation integration
原有未实现边界保持阻断；本slice可用controlled analyzer，不伪造human PASS。
没有运行真实fresh source或H3 A/B，也未核对当前两臂live输入与授权，不能宣称fresh accepted source为唯一前置。
旧FAIL/NOT_EVALUATED与S02/S03保留。
