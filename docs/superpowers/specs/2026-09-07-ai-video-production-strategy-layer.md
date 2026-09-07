---
surface_id: production_strategy_layer
canonical: false
spec_status: accepted
implementation_status: in_progress
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: production-strategy-layer/0.1
---

# AI-VIDEO Editorial / Production Strategy Layer Specification

## Status And Authority

Date: 2026-09-07。

本 Spec 来自当前源码、contracts、Director artifacts 与 S01 历史失败证据的调查。编写和独立审查后，
用户明确要求“实现”，随后要求“继续”，授权本 Spec 的代码与离线验证；当前实现与独立验证进行中。
此前禁止创建 implementation plan、Provider 调用、媒体生成、commit 或 push 的限制继续保留。
本次实现授权不授权操作既有真实 Production 项目，也不改变已批准的创作、调用范围或验收要求。

下文描述 accepted contract，不以本文状态替代执行验证。当前事实以
[runtime baseline](../../v0.2-runtime-baseline.md)、[contract matrix](../../agent-primary-contract-matrix.md)
及实际源码为准。当前 working tree 的 Generation Feedback implementation 是可复用基础，
本 Spec 不将其改写为未实现，也不以其源码或离线验证证明真实媒体质量收益。

本文补充 [Generation Feedback Orchestration](2026-09-07-generation-feedback-orchestration.md)
上游的生产选择边界：后者关于 Router 唯一选择者的契约继续适用于 generation candidates。
本文不取代其生成闭环，而是承接需要跨出生成范围的复评结果；相关 owner 文档
应在实现时同步这一限定，不能保留两份对同一决策都有最终权的契约。

## Problem And Evidence

核心缺口是：**已有导演拆镜和底层剪辑能力，没有共同的前置生产手段决策与可执行交接契约。**
系统需要回答“这个意图如何完成”，然后才对需要生成的部分回答“这次如何生成”。

| Evidence | Current observation | Implication |
| --- | --- | --- |
| [Director coverage validator](../../../.agents/skills/open-video/scripts/validate_director_coverage.py)、[Episode authoring](../artifacts/drama/jieshi-episode-01/episode-01.md) | 已有 single-take/multi-Shot coverage；S44/S46/S49 使用多个 generation components；S01 明写 clean plate | Editorial 思考已经存在，不能以“从零增加导演能力”为前提；自由创作描述不等于可执行 Production handoff |
| [VideoPlanner](../../../src/ai_video/planning/video_planner.py)::prepare_shot_for_existing_production | 交接一个 current_shot 和一个 generation_requirement | 缺少一个意图对应多个生产组件、多个执行分支的共同交接 |
| [ShotVisualResolver](../../../src/ai_video/production/_shot_visual_resolver.py)::resolve | 已选择 existing/static/image-motion/graphics/generated；EXACT_TERMINAL/REFERENCE 提前约束生成模式，existing reuse 仅在 continuity NONE 分支；hero/repair 阻塞 | 现有选择责任需要收敛，不能保留旧选择器再增加一个自主改判的上层 |
| [generation_difficulty](../../../src/ai_video/planning/generation_difficulty.py)、[generation_experience](../../../src/ai_video/production/generation_experience.py) | facts/features 用于生成经验比较；action_complexity 与 hand_prop_interaction 仍为 unknown | 这些事实不是 production strategy，未知复杂度也不是简单或不可生产的证明 |
| [GenerationFeedbackOrchestrator](../../../src/ai_video/production/generation_feedback.py) | 候选来自 registered video variants；重复失败能产生 SPLIT_SHOT；仅 GENERATE_ONCE 编译并进入执行绑定 | 已有生成复评和退出信号，尚无拆镜、剪辑、音频、素材复用方案的共同生产出口 |
| [AdCreativePlan](../../../src/ai_video/production/ad_creative.py)、[P6 composition repair test](../../../tests/test_production_base_ai_comic_e2e.py) | 广告已有 source/graphic/hero asset 表达；P6 已覆盖只改 composition、保留媒体身份的 repair | 上层语义与非生成修复有可复用模式，不能把所有 repair 描述为重生成 |
| [S01 H3 repairs](../../record_for_agent/2026-09-06-jieshi-s01-local-h3-bounded-repairs.md)、[H3-029 actual request](../../../runs/jieshi-s01-h3-horizontal-20260906-029/production/state/video-generation/requests/d7de0b52bfdb4a704a3c6e652e5a2bb687dc9cdd92f86ca69b82003d00d33d88.json) | clean-plate/composite 操作成为生成 prompt；反射与精确广播约束持续失败 | 制作操作被压进单次模型任务，支持重新分配生产责任；不证明完整生成在所有 Provider/recipe 下不可能 |
| [S01 local editorial preview](../../../runs/jieshi-s01-local-edit-20260906-001/REVIEW.md) | attempt07 音轨起点前移后，ASR 结束进入 2.64 秒；用户随后明确否决手部动作 | 后期能解决部分时序；旧“07 视觉可保留”已被否决，不能以剪辑掩盖动作 FAIL |
| [Historical rough-cut rejection](../../record_for_agent/2026-08-20-5-minute-rough-cut-editorial-failure-and-recovery.md) | 历史记录报告大量 reference-derived still 复用没有承载各 Shot 的独立意图，technical composition 未获成片验收 | 复用与非生成路线同样可能选择错误；更少生成、更多剪辑不是普遍更优的证明 |

审计基于 HEAD `4a5dc29` 与当时已有的未提交源码。S01 07/08/09 和 local preview 的文件 SHA/bytes
已在前序只读调查重核。Historical observations、当前代码和 proposed behavior 保持分离；OOM、
缺失人耳/人眼证据、quality FAIL 与 outcome unknown 不合并计数，也不据不同 recipe 的尝试推导因果胜率。

## Goal And Non-Goals

目标是在首次生产及需要复评时，基于 approved intent、当前素材、真实执行能力与适用证据，选择
能够保持导演意图的生产组合，并交给既有 owner 执行。完整生成是候选之一，剪辑也不是强制默认。

首个可验收实现至少必须贯通：无需 Video Provider 的已有素材裁切/组合与独立音频路径；确有缺失
动态素材时的生成分支；允许拆镜时的一对多 authoring handoff。只增加建议标签或输出自然语言
“请拆镜”不满足本 Spec。非生成候选必须能在没有 registered Video Provider 时被建立和选择。

本范围不包括通用 Agent Runtime、自动编剧、模型训练、UI/NLE、队列、新 Provider 或新 renderer。
不要求同时实现所有策略词汇对应的执行器；通用 mask/tracking/retiming/lip-sync 等能力缺口明确
返回给对应 owner，不通过 prompt、shell finalization 或静默 fallback 假装已有支持。

## Abstraction And Ownership

```text
Director / domain authoring
  -> approved intent + constraints + allowed transformations
  -> Production Strategy Resolver
       <-> method-specific feasibility / evidence assessment
       -> selected production composition and owner handoffs
          |-- existing asset reuse / trim / supported reframe
          |-- Generation Orchestrator -> existing Router -> adapter / service
          |-- audio / dialogue / captions
          |-- supported composition
          `-- explicit Video Edit / Extend capability, or capability gap
  -> existing CompositionSpec -> ResolvedTimeline -> HyperFrames
  -> existing Review / Repair / Final Acceptance owners
```

这是责任关系，分支可以组合；不是第二份执行调度图或新生命周期。

| Responsibility | Owner and boundary |
| --- | --- |
| 剧情、观看目标、空间证明、可接受取舍 | Codex + approved Character/Scene/Shot/domain artifacts；strategy 不自行改变 |
| 是否生成、怎样拆分生产、哪些素材复用、哪些要求交给音频/合成 | Production Planning 内的 ProductionStrategyResolver，收敛现有同类选择职责 |
| 已决定生成后的 inputs/interventions、受控尝试与结果回流 | GenerationFeedbackOrchestrator；不得自主新增剧情镜头、删除动作或替换对白 |
| exact Provider/model/capability/recipe ranking、selection 与 binding | 现有 VideoGenerationResolver；strategy 可消费其适配观察和已批准路线约束，不重复排名或预选后伪装为 Router 决策 |
| domain-specific presentation / source constraints | 既有领域 authoring；AdCreativePlan compiler 投影已接受选择，不被通用策略覆盖 |
| 素材身份、来源、可读取性与用途资格 | Asset Registry、既有 source/derivation readers 与 QA owners |
| 已选择的镜头次序、素材区间和时长意图的精确解析 | CompositionSpec -> ResolvedTimeline；唯一 frame/sample/timing/source-trim truth 不变 |
| dependency、precise invalidation、rebuild frontier | 现有 Dependency Graph / resolver；strategy 不保存另一份 desired/fresh/stale |
| durable write、effect permit、activation、recovery | ProductionStateCommitter 及既有 private implementation owners |
| required findings、repair scope 与 final acceptance | 既有 QA/P6/Gate；strategy 不能签发 PASS 或降低 frozen rubric |

Production Runtime 继续不 import Planning、Dev records、RAG、Skills 或 `.agent/playbooks/`。
Application caller 调用 Planning，传递 Product contract 允许的 immutable payload；Product owners
验证其当前引用与语义，不反向执行 Planner。具体类型放置须遵守现有 dependency direction。

## Intent And Production Unit Contract

必须区分三个身份，不能因为现在均使用“Shot”就合并：

- **Intent scope**：一个已批准 Shot 或有明确边界的相邻 sequence，保存要传达的事件、可见证据、
  continuity、时长/节奏、对白、观看目标及允许的变换；不新建平行 Story/Character/Scene 真相。
- **Presentation Shot**：观众最终看到的连续镜头。一个 intent 可对应多个 Presentation Shots，
  但 single-take、同框证明或其他不可分约束存在时，不能自动拆可见镜头。
- **Production component**：为上述镜头提供画面、前景、音轨、字幕或已登记片段的工作单元。
  一个 continuous Shot 可以使用多个 components；component 不必是一次 Video Provider 调用。

每个新镜头/组件必须绑定 parent intent identity、来源与承担的 requirements。拆分必须保留有序映射、
总时长约束、前后状态和对白关联。原 authored Shot 与 generation_components 不能只靠名称相似匹配。
新的 creative revision 由原 authoring/committer owner 封存；不能原地修改已接受 Shot 或旧 attempt。

## Strategy Vocabulary

策略不是一个平级互斥枚举。以下词汇用于描述方案，不表示当前执行能力全部存在。

| Dimension | Examples | Contract |
| --- | --- | --- |
| Coverage / shot design | SPLIT_SHOT、CUTAWAY、REACTION_SHOT、INSERT_SHOT | 说明叙事作用、前后状态与新镜头对原 intent 的覆盖；超出 allowed transformations 时需要 authoring revision |
| Source / production operation | GENERATE_FULL_SHOT、EXISTING_ASSET_REUSE、TRIM_EXISTING、EDIT_EXISTING_VIDEO、EXTEND_VIDEO、STILL_IMAGE_WITH_MOTION、COMPOSITE_MULTIPLE_ASSETS | 必须关联真实 source 与具体 executor capability；通用标签不能当能力证明 |
| Composition / sound operation | REFRAME、REPLACE_AUDIO、DUB_DIALOGUE | 区分固定重构图与 tracking、画外配音与口型修复；不得隐式删去镜头要传达的信息 |
| Generation intervention | CHANGE_REFERENCE_STRATEGY、CHANGE_PROVIDER | 同一生成任务内交既有 generation owner；若改变意图、连续性义务、Provider 授权或 egress 范围则先返回相应 owner |
| Authoring transformation | SIMPLIFY_ACTION | 标明丢弃/改变的信息与 protected requirements；不能仅因难生成就自动获批 |

同一方案可以包含“复用背景 + 生成前景 + 独立广播 + 合成”。更换 Provider 仍需原 quota、egress、
permit 等约束，不能把它包装成免费、无副作用的 editorial adjustment。

## Resolution Contract

### Inputs

Resolver 是 pure、bounded、deterministic decision：不扫描文件、不加载模型、不联网、不分析媒体，
不调用 Provider，不写任何 Product state。调用者从现有 readers 取得并验证以下 snapshot：

| Input | Required information |
| --- | --- |
| Intent | exact selected project/creative identities、目标范围、continuity 与 protected requirements |
| Allowed transformations | 已批准的拆镜、裁切、重构图、声音替换、动作简化边界；缺失授权不能解释为允许 |
| Existing resources | exact registered asset/source identities、候选帧/采样区间、来源/用途资格与适用 findings；未登记媒体只能作为缺口线索 |
| Capabilities | 各实际 executor 的支持范围与版本，包括 geometry、trim、图层、声音、edit/extend 等限制；不得从 enum、Skill 或营销名称推断支持 |
| Acceptance | 现有 generation_acceptance / domain_acceptance 及 evaluator/proof 绑定、跨组件与组装后要求 |
| History / limits | 当前 intent 及关联组件的 exact failures、unknown outcomes、已有决策、用户范围和 task quota 的只读投影 |
| Policy | 有版本的候选构造与选择规则、显式 tradeoff 与不确定性处理；不复制 paid ledger 或实时查价 |

### Candidate Construction And Feasibility

共同 candidate producer 必须消费 typed authoring、registered resources 和能力观察，有限枚举适用
生产组合。不能要求每个 run script 手写一个已经选好的 strategy，再让 Resolver 验证预设答案。
没有可靠语义理解时使用 authoring 明确提供的 requirement/coverage facts，未知部分保留 unknown。

Feasibility 针对每个候选分别判断：语义覆盖、技术可执行、来源可使用、证据是否足够、质量不确定性
以及执行范围。不得先给整个 Shot 一个 scalar difficulty，再按阈值硬编码 full generation 或 split。
生成经验仅由原 generation owner 提供适用范围内的观察，不外推成剪辑/合成成功概率。

选择遵守以下顺序约束：先排除违反硬约束和缺失必需资格的候选，再比较有证据支持的质量适配与
生产负担。只有都满足 protected requirements 时，复用已合格素材、减少新增 effect 才能成为偏好。
不得仅以“零生成”或“最少镜头”为最优；不得用固定 Provider 排名、文件顺序或 candidate ID 打破实质性平局。

语义质量尚未实测与必需证据缺失是不同情况：前者可以在既有明确 policy/授权下选择有界探索，
必须标注其未验证；后者不能被冒充已合格素材进入执行。没有可区分的方案时保留 unresolved choice。

### Output And Freshness

逻辑输出包含：input/policy identity、候选与排除理由、选中方案、组件/镜头映射、requirement allocation、
exact source selections、executor handoffs、protected requirements、unresolved items 与 review obligations。
这些是合同内容，不要求一字段一 class，也不预设新的 Manifest layout。

输出必须区分 selected、needs authoring revision、evidence required、capability gap、unresolved choice、
blocked scope 和 recovery required。Selected 表示方案选择，不是 submit permit、activation 或质量验收。
选择不创建任何 attempt。缺失 executor 的候选不能产生伪装为可执行的 handoff。

Application 在 materialization/effect 前重新打开上下文并重算必要决策；原 Product owner 继续在其
transaction/permit 边界验证 exact revision/hash，阻止检查后漂移。Strategy evidence 若需持久化，
只能作为既有 owner 管理的 immutable evidence；不得增加 status 文件、progress store、另一份 DAG
或“上次已选择，所以可以直接运行”的恢复路径。任一必要 additive schema 扩展必须有显式 compatibility
contract、reader/recovery 与 tamper tests，不能藏进未验证 extra fields。

## Requirement Allocation And Evidence Reuse

当前 `generation_acceptance` 与 whole-output `domain_acceptance` 已经分离，继续由原 acceptance
owner 独占。Strategy 提出的是生产责任分配；acceptance owner 验证后才能封存为各阶段的要求。

每个最终 required requirement 必须有明确实现组件、验收阶段、proof owner 和 exact evidence binding。
跨组件关系必须在组装结果上验证，例如人和倒影的几何关系、音画对应、切镜连续性、最终字幕和广播时序。
不能把多个源的局部 PASS 拼成虚构的 whole-output PASS。

在首次生成前明确 source/raw 与 assembly/final obligations。不得因为某次 raw FAIL 才自动把该要求
移到后期、改成 hint 或删除。改变分配必须由原 owner 完成显式 revision；旧 rubric、旧 bytes 和旧 verdict
保留，新组合重新验证。当前 Per-Shot Gate 不被 strategy decision 替代。

失败视频可能含有可讨论复用的声轨或区间，但整个源并未因此被接受。只有 exact 用途、区间、来源与
qualification 经既有 owner 验证，才能进入新目标；没有可表达该用途的 canonical registration/derivation seam
时返回 capability gap。禁止把 generated source 改标 imported，或为了取音轨激活失败视频。

连续生成仍须在每个新 exact MP4 后执行 project-local video-analysis 和全部适用 required findings；
FAIL/NOT_EVALUATED 阻断下一 Shot submit。拆分后的原 intent 还需完整组装验收，才可被声明完成或作为
已接受的下游连续性来源。新组件 ID、Shot revision 或新 strategy hash 不能抹去相关旧失败、unknown outcome
或重置同一任务额度；parent/component lineage 必须由原 owner 的可重开证据保留。

## Execution Handoff And Existing Capabilities

| Branch | Handoff | Current limit to preserve |
| --- | --- | --- |
| Existing asset reuse / trim | registered exact assets + ordered composition requirements + source selection | H.264 MP4、交付 geometry/FPS 与精确覆盖约束；不是任意文件或自动挑选片段 |
| Supported reframe / composition | CompositionSpec layers、fixed transforms、graphics、CUT requirements | 不具有通用 mask/tracking/occlusion/retiming；P3 当前不接受 IMAGE_MOTION/HYBRID visual_strategy 或任意 motion_directives |
| Audio / dialogue / captions | P4 audio tracks、sample trim/mix intent、caption bindings | 视频元素保持 muted，最终声音由同一 timeline/mixer 消费；配音不自动证明 lip-sync |
| Native audio derivation | existing generated-video-audio owner 的 exact source request | 当前要求 settled remote/metered source，target Manifest 2.0–2.2 / Registry 2.1；不能绕过或假定适用于所有项目 |
| Generation | 经当前 authoring/Planner/readiness 的 component requirement，再交共同 generation caller | 保留 Router selection、native compiler、execution binding、Service/Committer 和原 effects gates |
| Video Edit / Extend | 已选择的生产操作、exact source 与适用 Provider capability | 复用已有部分 adapter 支持；不得推断通用局部编辑能力或自动更换 Provider |
| Missing capability | 精确缺口、受影响 requirements、对应 owner | 不执行，不自动变成 full-shot regeneration，不创建临时 shell finalization |

只有确需的新素材进入 generation；已有非生成方案的准备不得依赖 Video Provider 注册、secret、
pricing、generation quota 或无关 generation evidence。若复用来源本身是 paid artifact，其原有来源验证
和结算要求仍然适用；零新增 Provider call 不消除既有 provenance obligation。

## Integration And Retirement Contract

新实现归属 Production Planning，现有 choice responsibilities 必须在同一 integration scope 收敛：

- `ShotVisualResolver` 中决定生产手段的规则应迁入或被新 owner 替代；剩余 Production helper 只能提供
  compatibility observations，不能在 selected strategy 后再改判。不得用 Production -> Planning import
  实现回调。旧 public selection caller 的迁移/retirement 必须明确并测试。
- `VideoPlanner` 保留生成组件的 requirement planning；EXISTING_VIDEO 不再被统一送进其 dynamic lane。
  保留 generation-specific mode/reference 约束，移除与上层同义的自主生产手段决策。
- `GenerationFeedbackOrchestrator` 复用原生成闭环；SPLIT_SHOT/REASSESS_FEASIBILITY 等信号交共同
  production strategy caller，由它产出新候选或明确 blocker，不建立独立拆镜策略引擎。
- Director/AdCreativePlan 提供已接受意图和领域约束；其 compiler 投影同一选择，不能与通用层争夺
  presentation/Shot order。现有领域验证不被通用启发式替代。
- `.agent/playbooks/composition` / composition shadow 继续是 Development advisory；不得让 Product
  直接读取或将 shadow proposal 的 hash 偷渡为 runtime truth。保留既有 shadow-to-runtime integration
  的证据要求，新增 Spec 本身不证明其 Pilot 已完成。
- Public production caller 必须有明确的非生成与生成 handoff；run scripts 不再拥有第二套生产策略。
  专用底层执行 API 只消费明确选定的操作，不因命名“通用”而获得重写导演意图的权限。

Legacy CLI 及其独立控制路径保持兼容。已有 sealed requests、artifacts、replay/recovery 继续按原身份重开，
不被强制重新规划。历史 source reader 与恢复能力不能因旧选择路径 retirement 被删除。

## S01 Conceptual Case

保留当前原始悬念：“林砚，请在终点站下车。”、前三秒异常、既定字幕、其他乘客有倒影且林砚没有。
当前 accepted hand-repair scope 还保留 native audio、锁机位、右手手机与手部动作要求；本 Spec
不修改它，也不恢复已撤回的普通报站方案。参见 [current repair direction](../artifacts/drama/jieshi-episode-01/s01-repair-direction-20260907.md)。

首选比较“保持 continuous Shot、拆生产组件”，无需先增加可见切镜：

| Component | Candidate operation | Required evidence / limitation |
| --- | --- | --- |
| 背景、窗框、七名他人倒影 | EXISTING_ASSET_REUSE；确有需要时使用真实 clean plate | 必须复核 exact 区域与几何；不假定任何旧完整视频已合格 |
| 林砚与左手动态 | 检查现有片段；需要修复时比较局部 VIDEO_EDIT 与独立前景生成 | 手型、掌向、运动和右手手机必须单独满足要求；旧 endpoint 的疑点不是已证实因果 |
| 缺失自身倒影 | 实际 plate/mask/composite，或已充分验证无需处理的源 | 当前通用遮罩合成能力不足，返回 capability gap；禁止把“composite”再仅写进生成 prompt |
| 点名广播 | 优先现有 native track 的合格裁切/位置调整；替换仅在允许范围内提出 | 保留原句与声音偏好；字音、起音、音色、混音需要适用证据，ASR 不替代人耳 |
| 叙事字幕与最终前三秒 | P4 + canonical composition | 保留既定文字和时间；不让 Video Provider 随机生成文字 |

实际 attempt07 音轨前移的 local preview 已让 ASR 结束进入 2.64 秒，但其手部后来被用户否决。
因此它仅支持“声音时序可以独立修”的有限观察；不能把 07 前三秒当现成 PASS，也不能把该
非 canonical FFmpeg preview 当作 HyperFrames/P6 proof。候选若缺合格手部素材或合法来源入口，
正确结果是仍未具备完整执行条件。

只有 authoring 允许改变镜头组织时，才比较“异常 master -> 保留玻璃关系的手部 insert -> reaction”。
拆镜后仍需证明本人存在、对应倒影缺席、其他倒影存在；切走本人或玻璃不能冒充原同框证据。
必须维持原总时长与后续 S02 状态，不能用静图替掉必需抬手动作。横版 H3 preview 也不能自动
成为竖版交付素材。以上均为待验证生产假设，没有新的媒体质量结论。

## Acceptance And Verification

| ID | Required behavior and proof |
| --- | --- |
| PS1 | 从 standard loaded project、typed authoring、registered assets 经真实 candidate producer/Resolver 到 handoff；不以测试手填 selected strategy 代替生产者存在 |
| PS2 | 无 Video Provider 配置时，合格已有视频 + trim + 独立音轨/字幕方案进入 canonical composition fixture；Video Provider construction/start/submit counters 为零，无 secret/egress 访问 |
| PS3 | 合格完整源、完整生成、分层方案均可成为候选；在相应证据/约束下选择不同路径，证明不存在 always-generate 或 always-edit 默认答案 |
| PS4 | 只有缺失动态组件进入原 Planner/Router/generation binding；已有组件 identity 不变；不绕过 generation acceptance、permit、quota 或原 Per-Shot Gate |
| PS5 | allowed split 生成有序且可 materialize 的多镜头 handoff，总时长与 requirement coverage 保真；single-take/同框证明/禁止改对白反例不得自动放行 |
| PS6 | 已支持的 trim/reframe/图层进入同一 ResolvedTimeline；mask/tracking/任意静图运动/不支持的 edit 被识别为 capability gap，无 shell 或生成 fallback |
| PS7 | 只有音频时序需要修复时保留合格视觉；若视觉也有 human FAIL，则不得复用为已合格动作。覆盖 S01 07 preview 的后续人工否决反例 |
| PS8 | generation/final requirement allocation 完整且由原 acceptance owner 验证；漏项、未经显式 revision 事后移动 FAIL、跨 artifact 拼 PASS、移除可见空间证据均拒绝；覆盖经原 owner 新 revision 合法重新分配、保留旧 verdict 并完整重验新组合的正向用例 |
| PS9 | exact source/window/role 变化、proof stale、未登记来源或 derivation/target 不兼容均 fail closed；不得激活失败源或伪造 imported provenance |
| PS10 | 对相关输入、policy、capability、source/QA revision 的漂移，旧 decision/handoff 在 effect 前失效，不能据它获得新 permit 或 effect；重新打开当前上下文后可产生新决策，再走原 gates；同输入解析可重复 |
| PS11 | 拆分/改名/换 strategy 后保留 parent lineage、相关 failure history 与 task quota；unknown outcome 必须先显式恢复；重启不重放已完成 side effects |
| PS12 | composition/audio repair 只触发 P5 计算出的相关 rebuild，非受影响素材保持身份；新组合经 P6 验证，不能手写 FRESH 或复制旧 acceptance |
| PS13 | 当前 legacy、historical request/recovery、领域 authoring 正向用例继续成立；同类 strategy choices 只有一个 owner，Product 无 Planning/Dev 反向依赖 |
| PS14 | 没有可区分候选、必要 authoring 取舍或 proof 时给出具体 unresolved/blocker，不靠排序、假概率、自动放宽约束或新 Provider call 得出答案 |

未来实现的 focused verification 应复用 planning/router、generation feedback、composition/audio、
repair/Project/State/P5 tests 和 standard fixtures，再增加上述真实跨分支用例。模拟外部 effects
不能同时模拟掉 candidate construction、requirement allocation、标准 loader 或 owner handoff。
最终 checks、exact snapshot 与 receipt 路由由 Harness policy 决定，不能由 Spec 宣称通过。

Engineering acceptance 与 empirical benefit 分开：前者证明选择、交接、身份与拒绝路径；后者需在
后续适用授权或 local exemption 下，以冻结意图、rubric、baseline、资源/submit ceiling、观看条件和
完整失败记录比较成片可用性。减少 submit、单个成功案例或提前停止本身不证明整体质量提升。
本 Spec 编写阶段不运行该实验，也不以 S01 的旧媒体替代新策略验收。

## Completion Boundary

本方向值得在继续扩大 Generation Orchestrator 的整体生产职责前优先实现，但必须同时交付
可运行的非生成出口与原 choice responsibility 的收敛。只有一个新 class、更多 FFmpeg options、
一个 SPLIT_SHOT disposition 或一段 editorial 建议，不构成本 Spec 的完成。

本文已写入并经过文档检查，用户后续接受其实现；这不代表代码已实现。
超出本 Spec 的 schema/API 变化、代码验证、真实执行、human/P6/Final Acceptance 与发布状态
仍须分别满足对应契约。
