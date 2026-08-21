# Quality Intelligence Data Foundation Start Gate

Date: 2026-08-21

## Decision

Quality Intelligence 的**数据基础从现在开始建设**，并且必须在下一次 4～8 Shots、
30～60 秒真实 Pilot 之前具备最小可用形态。

这里的“开始建设”只指结构化采集、可比实验设计、证据绑定与人工 verdict 记录；不指
自动学习、自动选择 Provider/profile/参数、自动提交生成、自动 repair，或自动作出 P6
Review / Final Acceptance。

下一次获授权的 quality experiment 不应继续只产生散落的文字笔记。它应同时产生一份
与 exact request、resolved generation、artifact bytes、测量结果和人工 verdict 绑定的
结构化 experience record。既有 durable records 继续作为历史证据，不为填充新 schema 而
回写、猜测或伪造缺失字段。

## Why The Start Point Is Now

当前已经积累了足够证据来定义采集边界，但不足以训练或授权自动决策：

- Local H3 Alice A/B 已暴露 reference 分辨率、输出尺寸、CRF 与二次编码对清晰度的影响；
- T10 单 Shot、约 15 秒动作突变 `NO-GO` 及 motion-continuity repair `GO` 已形成一组
  failure -> intervention -> human verdict 案例；
- Hailuo C2 已出现 `pass with minor concerns` 和轻微 facial variation；
- T8 Turbo/Quality smoke 已有耗时、显存、音频、detail metrics 与 confounded-variable
  边界；
- P6 已提供 Review / Repair / Final Acceptance 的 canonical lifecycle owner。

如果继续实验而不先统一字段，后续案例会继续难以比较；如果现在直接建设自动学习或
自动选参，则会把少量、非盲测且存在混杂变量的案例过拟合成错误策略。

## Q0 Data Foundation Scope

首个阶段命名为 `Q0 passive capture`。每条 experience 至少绑定：

| Domain | Minimum captured truth |
| --- | --- |
| Experiment identity | experiment ID、timestamp、repository commit、purpose、authorization boundary |
| Shot context | project/Scene/Shot IDs、shot class、visual strategy、continuity mode、open/close state |
| Inputs | exact Character/Scene/reference asset IDs、content hashes、first/last-frame binding |
| Planning and routing | request/plan/requirement/readiness/Router selection hashes与exact Provider capability |
| Generation | profile/workflow/binding/model identities、prompt identity、seed/effective seed、尺寸、帧数、fps、steps、sampler/scheduler、audio mode |
| Artifact | canonical或lab边界、path、SHA-256、bytes、codec、`ffprobe`、activation/reopen/replay state |
| Measurements | selected `video-analysis` evidence、black/freeze/scene/audio/detail/continuity measurements及工具版本 |
| Human review | reviewer identity、rubric version、逐项 verdict、GO/NO-GO、concerns、观察时间点 |
| Intervention | failure taxonomy、changed variables、unchanged controls、confounders、repair rationale |
| Outcome boundary | exact artifact acceptance、P6 receipt/freshness（若存在）、不得外推的结论 |

Raw credential、signed URL、secret、完整 Provider response与不必要的 raw prompt不得进入记录。
Prompt可以保存 content-addressed identity、结构化意图和必要的动作阶段；是否保存原文必须遵守
现有 provenance、隐私和 durable-record contract。

## Experiment Discipline

Q0 启动后，quality experiment 必须遵循：

1. 生成前声明 hypothesis、rubric、主要变量和保持不变的 controls；
2. 参数或 prompt 变化若机械改变 seed，必须标记为 confounded，不得称 single-variable A/B；
3. 自动指标只作为 technical evidence，不得替代完整观看和人工 verdict；
4. `READY`、submit/fetch success、artifact activation 与 quality acceptance 必须分开记录；
5. 同一次失败只允许提出可追溯到 evidence 的 bounded intervention；
6. repair 后必须生成新的 exact experience，不能覆盖失败案例；
7. 任何 remote/paid experiment 仍独立经过 budget、egress、secret、permit 与用户授权 gates。

## Advancement Gates

### Q0 -> Q1 Advisory Recommendations

只有同时满足以下条件，才开始建设只读、可解释的建议层：

- 已覆盖 task 所需的代表性 Shot classes，而不是只覆盖同一人物和同一动作；
- 每个拟议建议至少有可复现的成功/失败对照或跨案例重复证据；
- experiment records 字段完整、hash 可重开、rubric 和 verdict 可追溯；
- 已明确哪些规律只适用于 exact Provider/profile，哪些可能跨 Provider；
- held-out Pilot review 表明建议不会系统性降低 identity、motion、continuity、audio 或 pacing；
- 建议层只返回 rationale 和 bounded options，不修改 Planner、Router、Manifest 或 Provider state。

### Q1 -> Q2 Constrained Local Parameter Search

只有 advisory recommendations 经独立回顾验证后，才考虑在 local/unmetered、明确白名单的
参数空间内进行受控搜索。Q2 仍必须保持 deterministic experiment lineage、预算/资源上限、
人工 GO 和无自动 activation；不得借此建立第二个 Router 或 P6 owner。

### Automatic Provider Selection Or Final Acceptance

当前没有 start date，也未获批准。任何未来自动 Provider/profile selection 都必须先有独立
Spec，保持 Router exact-selection、no-fallback、paid authorization 与 provenance contract。
Quality Intelligence 永远不能仅凭历史经验自动提交 remote/paid request，或替代 policy-selected
human/evaluator 作出 semantic PASS 和 Final Acceptance。

## Immediate Next Application

下一次 4～8 Shots Pilot 是 Q0 的第一个 prospective dataset，不是训练集完成证明。Pilot 应覆盖
至少人物近景、较大全身动作、一次 Shot continuity handoff、光线或景别变化、native/generated
audio 与最终 composition；逐 Shot 和整段分别记录 identity、motion naturalness、continuity、
camera、lighting/color、spatial storytelling、audio、caption readability 与 pacing verdict。

在该 Pilot 之前，只需完成最小 schema/validator/serializer/fixture 与记录落点的独立 Spec/Plan；
不得为了“Quality Intelligence”扩大为数据库、在线服务、模型训练、自动 Provider loop 或新的
quality gate。

## Current Boundary

本文件是 timing/ownership decision record，不是 runtime implementation、schema acceptance、
Provider authorization、Pilot GO、P6 Review receipt或Final Acceptance。它不改变
`ShotReadinessGate`、Video Planner、Router、Provider、Registry、Manifest、
`ProductionStateCommitter`、P6 Review/Repair、`ResolvedTimeline` 或 HyperFrames ownership。
