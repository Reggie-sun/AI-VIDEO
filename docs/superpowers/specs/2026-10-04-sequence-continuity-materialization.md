# Sequence Continuity Materialization

## Goal And Owner

基于 `a0682cbd`，让结构化 authored adjacency 在 Planner 前成为 existing previous state/policy v2。
顺序 owner 是 `Storyboard.beats[].shot_ids`；composition/timing owner 不变。
Planning 的 `sequence_continuity` adapter 是唯一通用 edge materializer；复用
`VideoPlanner.derive_previous_shot_state` 与 `ContinuityTransitionPolicy.create`，不增加 schema。
当前 repo 没有 Canvas UI/model；标准 authoring API 适用于 Canvas method 和其他 sequence caller。

## Semantic Truth

显式 authoring 提供 existing boundary/obligation/semantics、take、完整 `CausalStateChange`。
source close 来自 activated attempt 的 strict-reopened execution binding 中的 authored intent，
FULL另须既有QA recipe绑定`generation_intent.close_state.state_hash`、exact observable/tolerance，
由现有analyzer/human评价证明该完整column已达到；activation或技术PASS不证明causal close。
target open 来自 sealed target `ProviderNeutralGenerationIntentProjection`。
两端用既有 `TypedStateReference(kind=TYPED_HASH)` 封存按 dimension 排序的 causal column hash。
只核验 caller 已声明的十项 facts；不从 state_text、prompt、角色名或相邻位置推断。
`CARRY` 必须两端相等；visible change 必须用既有 bridge，release 服从 v2 semantics。
没有完整 hash-bound causal declaration时为 `PLANNING_PREFLIGHT_BLOCKED / NEEDS_AUTHORING_EVIDENCE`。

## Previous State And Policy

canonical loader选择 target 与紧邻 source，严格匹配 expected source artifact/revision/content hash
及 source generation intent hash；source 已 activation 且 exact media evaluation PASS。
policy source identity是生成该 accepted media 的 sealed authored Shot identity；current activated Shot
通过既有 activation lineage重开验证，不能把 activation 后 revision伪装成生成前 identity。
terminal availability只来自 registered/exact source evidence。same take 调用 existing derive helper，
`same_action=True, angle_change=False, semantic_jump=False`；hard cut FULL 调用该 helper，
`same_action=False, angle_change=True, semantic_jump=False`。carryover不带 same-action承诺。
reset允许 previous=None。

policy v2绑定 current Project/Registry、source/target、两 intent hashes、实际 supplied route-bound
stacks、boundary/obligation/semantics、十维 changes、required carries、anchors、QA/authoring evidence
及 existing policy hash。未知 stack不创建 policy，不引入中间 semantic schema。
reuse existing `ContinuityProviderRouteBinding`，不直接构造 ProviderBoundVideoRequest。
该既有 binding additive保存 source activation Registry pointer，None省略以保持旧hash；
policy仍绑定target current snapshots。`production/_sequence_source.py`只读重开source proof，
不创建edge；feedback、public resolver、execution boundary共用同一校验，pointer本身不授权。
new Production preparation/execution对每条routing都要求activation pointer，旧字段省略不能跳过
source proof；无current-project的legacy pure compatibility prediction不授权新执行。
handoff重验source/destination实际stack，feedback另重验authoring seal。
已复现 Router legacy semantic-state必填会误封已验证v2 edge；只让validated v2替代该重复证明，
合法v2 identity/style REFERENCE不要求terminal；FULL仍要求terminal和实际frame conditioning。
不改Provider conditioning gate、legacy checks或选择规则。immutable binding replay保持pure，
current-project校验在preparation/execution边界执行，不能用pure预测结果代替activation证明。

## Classification

| Authored Declaration | Previous Flags | Existing Planning Lane |
| --- | --- | --- |
| WITHIN_CONTINUOUS_TAKE / FULL / DIRECT | same action, no angle change | EXACT_TERMINAL + original terminal I2V |
| HARD_CUT / FULL / DIRECT | angle change, no semantic jump | REFERENCE + target-derived FIRST_FRAME I2V |
| HARD_CUT or SCENE_BOUNDARY / IDENTITY_STYLE_CARRYOVER | reference/semantic | soft Ref2VA remains legal |
| SCENE_BOUNDARY / SUBSTANTIAL_RESET / SCENE_RESET | no required previous continuity | NONE remains legal |
| explicit independent (no edge declaration) | previous=None | independent route remains legal |

## Fail Closed And Handoff

adapter所有 semantic inputs都无 silent FULL/reset默认；independent须显式选择。
缺 source accepted state、identity/hash mismatch、缺 causal declaration、state hash drift、未 materialized
stack、缺 registered anchor/derived keyframe均 block。没有 derived keyframe时进入现有 C2 preparation
所需补证条件，adapter不生成/导入/伪造图片。
request additive嵌入 existing policy，旧 None序列化省略以保留旧 hashes。
`require_current_video_plan` 默认消费嵌入policy，显式传入冲突policy拒绝；production handoff保留同一policy。
feedback helper显式接收并转发 existing route binding，缺失或与 request policy不符阻断。

## Scope And Non-Goals

只修改 sequence→Planning/readiness/feedback handoff和已复现的 source snapshot/重复state阻塞。
freshness lookup用exact asset+owner identity，避免同一注册图的character/scene证明互相覆盖。
不重写 Planner/Router/capability；不改 FULL conditioning gate/METASO/Provider/prompt compiler。
不新增 GenerationUnit/StateContract/ContinuityGroup/NarrativeState；不新建 durable state writer。
不调用 Provider/credential、不生成真实媒体、不修改历史 evidence、不 push/release。

## Verification And Self Review

十项用户回归和 source activation/snapshot推进、policy丢失、legacy hash兼容测试。
targeted suites、Architecture Gate、exact staged changed-path Harness。
本任务涉及 accepted lineage/preflight，按 T3 同一 stable snapshot双独立 native read-only final review；
Kimi因当前 no paid/credential scope不适用。Parent复现裁决所有 blocking findings。
Self-review：既有模型已足够，state_hash只绑定 explicit typed facts，不新增 schema或 prose classifier。
