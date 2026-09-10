---
surface_id: s01_failure_recovery_strategy_regression
canonical: false
spec_status: accepted
implementation_status: foundation_only
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: s01-failure-recovery-strategy-regression/0.2
---

# S01 Failure-Recovery Production Strategy Regression

Date: 2026-09-09

## Status And Scope Change

本 spec 按用户的新目标修订：S01 不再用于“必须生成到 PASS”，也不再先选定一次
Seedance VIDEO_EDIT 实验，而用于验证真实失败后的 production responsibility 重分配。

验收对象是新 workflow 的实际决策与安全停止行为。正确、有证据的 capability gap
可以通过本轮 decision regression，而 S01 成片仍为未完成；两种状态不得混用。
文件路径保留以免破坏既有引用，旧 /0.1 的单次 Provider edit 目标由本修订取代。

用户随后以“实现”批准有界工程实现。目前仅完成只读 admission/history observation
foundation，入口为 `scripts/s01_strategy_regression.py`；没有完整 workflow PASS。
Provider、生成/派生媒体、真实 Production state mutation、commit/push 仍未执行。
真实 S01 缺 `production_intent`、allocation 与用途合格证据，返回
`integration_incomplete`，不得伪报 localized executor `CAPABILITY_GAP`。
当前历史与旧 context binding 的 limits/policy 分开标注，报告不验证当前执行授权。

### Approved Development Admission Follow-up

用户以“可以”批准仅在新开发 root 接入 attempt11 exact bytes 和可验证失败来源。
通过原 bootstrap writer 创建未绑定 `NOT_EVALUATED` repair input；不可将 imported
registration 解释为 source-use qualification、history admission 或 activation。
授权仅覆盖该专用接入与验证，不修改原 S01 项目、历史或预算；不调用 Provider、生成
或派生媒体、commit/push。该批准取代前述“尚未授权新增接入契约”的历史边界，不扩大为
通用 import/edit subsystem。当前进度由 runtime baseline 与主记录维护。

## Goal

从真实 S01 失败与原始证据出发，实际走既有 Production Planning / Generation Feedback
入口，验证三个问题：

1. 能否识别哪些内容值得保留、哪些要求仍 FAIL 或 NOT_EVALUATED，而不是默认整镜重生成。
2. 能否把责任分为可保留的视觉内容、原广播、待修的手部动作和 whole-shot assembly，
   并准确区分“分析上可分工”与“runtime 已能表达、materialize、执行”。
3. 当局部修复无法执行时，能否返回可归因的缺口并停止，不继续整镜抽卡。

本轮目标是有证据地避免不成立的整镜重生成，不是禁止所有未来 full generation。
真实可用率、成本下降幅度与局部编辑质量仍需后续媒体验证，不能由零 submit 单独证明。

## Verified Regression Evidence

主案例使用 attempt11，attempt12/13 与被拒绝 derivative 作为后续反例和保护项来源。

| Evidence | Meaning And Limit |
| --- | --- |
| attempt11 SHA-256 cb73c70c1e935d6849b3a91f5fa7ff19d81966647afaf88a010cd00dc89be537；3,297,401 bytes | exact source，历史实测 1080×1920、24fps、97 frames、约 4.042s、H264/AAC；运行时须重核 bytes/probe |
| attempt11 human legacy-06/14/17 PASS | 用户确认手部自然、玻璃间隙可读、广播清晰完整；不是全部视觉要求或整个环境 clean plate 的人类认可 |
| attempt11 legacy-03/05 FAIL | 约 1.25s 起手、约 2.5s 近目标；1.5s 未到位，腕部/掌向问题保留在正式历史 |
| attempt11 其他 11 项技术/抽样要求 PASS；窗内下部暗影另有 concern | 不自动把整个主体/背景标成可无条件复用；用途、区域与完整时间段的证据须匹配 |
| 后续首末图/抽帧复核指出指轴方向不等于掌面方向 | 不改写 attempt11 正式 FAIL，也不把历史解释当作已完全校准的掌向检测；分析不确定性必须保留 |
| attempt12 自然度/间隙/广播后来也有独立人类 PASS，timing FAIL、掌向 NOT_EVALUATED | 不能混用 attempt11 和 attempt12 verdict；不因 attempt 更晚就默认改基底 |
| speed-up + clone tail 被用户拒绝 | “手悬停”不等于“整幅画面冻结”，已知整体退化应在执行前淘汰 |
| attempt13 简化 prompt 后 timing 仍 FAIL | 该次干预无效；没有证明模型硬上限，也没有证明局部编辑必然成功 |

证据：[S01 history](../../record_for_agent/2026-09-08-jieshi-s01-human-gap-history-boundary.md)、
[attempt11 human confirmation](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v3/attempt11-human-confirmation.json)、
[attempt11 Gate](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v3/shot-01-gate.json)、
[attempt11 closure](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v4/attempt11-closure.json)、
[attempt13 compiled comparison](../../../runs/jieshi-e01-i2v-20260907-attempt10/preparation-v5/compiled-comparison.json)、
[rejected derivative](../../../runs/jieshi-s01-retime-review-20260908-v1/human-rejection.json)。

历史明确指出“立即抬手/稳定腕部”已经出现，不能把同义强调包装成新 intervention。
但 attempt11 关闭时未运行新的 Router decision；不能把 Agent 的拒绝理由描述成已验证的
自动 history-to-Strategy veto。这个接线正是本次要检查的行为。

## Current Runtime Boundaries

| Surface | Current Fact | Regression Implication |
| --- | --- | --- |
| ProductionPlanningService.prepare | strict load 后 resolve；不创建 intent、allocation 或 source-use evidence | 不会自动把历史 S01 变成可规划案例 |
| ProductionStrategyResolver | 枚举 authored coverage/source options；每个 unit 自动附加 full-generation；按 generation count 等既有 policy 选择 | 不能把人工创作 alternatives 描述成 Resolver 自主构思 |
| Failure history | prepare 不直接读质量 FAIL 和已失败 intervention；reassess_generation 校验 exit 后重开原 intent | 必须指出哪一个原 owner 真正消费 history；缺接线不能伪称闭环已完成 |
| ProductionUnit / Coverage | units 是顺序呈现 Shot；single_take/co_visible 禁止多 visual units | hand component 是分析责任，不是已有独立共时空间组件 |
| required_operations | 同一 unit 的要求影响其所有 source/reuse/generation options | 给 unit 加 MASK_COMPOSITE 使所有 options 失败，不证明公平比较后选了局部修复 |
| SourceUseEvidence | exact asset、用途、window、transform、requirement、proof/actor 绑定 | 旧整镜 human PASS 不自动成为新局部 source-use PASS |
| P3/P4 | trim、固定变换、固定 layers、CUT 和独立音轨组合已有 executor | split/cutaway/insert 不是全都缺失，但不适用于本 S01 的连续共视约束 |
| Provider-native edit/extend | 底层已有部分能力；Strategy 不支持对应执行分支，S01 适用性未验 | gap 必须指出层次，不能写成所有 video edit/extend executor 都不存在 |

源码：[Strategy](../../../src/ai_video/planning/production_strategy.py)、
[Planning service](../../../src/ai_video/production_planning.py)、
[production contracts](../../../src/ai_video/production/production_strategy_contracts.py)、
[source-use evidence](../../../src/ai_video/production/source_use_evidence.py)、
[materialization](../../../src/ai_video/production/production_strategy_materialization.py)。

当前顶层 disposition 可能是 evidence_required、needs_authoring_revision、capability_gap
或 blocked_scope；候选里的实际 blocker 比单个顶层名称更重要。schema 拒绝、缺 allocation
或缺原始评价不是“局部编辑 executor 缺失”的同义词。

本轮通过标准 load_production_project 只读重开
runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10/project.yaml：
selected S01 的 production_intent 与 production_lineage 均为空，production_allocations
和 production_source_evidence 均为 0，Registry 未找到 attempt11 exact MP4 的资产绑定。
这证明当前真实案例尚缺输入/authoring 接线；不代表没有历史原片或评价。
本轮未执行完整 Strategy regression，不能从这次加载检查宣称它已通过。

## Production Responsibility Allocation

下表是需被证据检验的候选责任分配，不是预先封存的 selected solution，也不是新 runtime schema。

| Responsibility | Preferred Source / Action | Required Qualification |
| --- | --- | --- |
| 角色、环境、机位、镜面关系 | attempt11 作为保留基底候选 | 保留已满足要求与暗影 concern；无法确认可分离区域时标证据/能力缺口 |
| 广播 | attempt11 原音轨优先保留，原句“林砚，请在终点站下车。”不改 | exact 音轨身份、内容、时序、音画关系及合法音轨入口 |
| 抬手时序、掌向/腕部 | 仅修未满足动作要求；评估 local edit / replacement | 局部可控性、输入资格、持续动态及与原画面的结合能力，不能只给 strategy 名 |
| 自然悬停和环境尾段 | 保持真实动态，不全局加速或 clone tail | 动作到位与自然尾段两者都满足 |
| Whole-shot assembly | 既有 composition/audio/timeline/QA owners | 原 4s、single-take、co-visible、字幕与完整 frozen requirements 不变 |

必须逐项标识“值得保留”“用途证据合格”“可 materialize”“能执行”“需最终重验”。
不能把整段含错误手部的画面当作无手 clean plate，也不能直接叠加第二只手；
没有 region isolation、tracking 或合适 source 就如实报告，不能用 fixed reframe 冒充。

不删 requirement 来让 source coverage 完整；无法映射到现有 component/allocation
结构时，记录 representational/authoring gap，不自动发明 component graph。

## Regression Contract

### Exact Inputs And History Projection

后续验证须通过标准 loader 打开真实 selected S01、attempt11 exact media/history、
完整 frozen QA，并同时核对当前最新 attempt/预算/unknown outcome，不能回滚到旧 snapshot
规避现在的 lifecycle。历史 r38 可以作为有明确来源的观察切片，不是当前可写 Production root。

attempt11 是保留素材和失败事实基底，不是强制覆盖 Feedback 的 latest/baseline。
GenerationFeedbackOrchestrator 的 project history 按当前目标 Shot 的 effective history
选择 latest 与 baseline_request；验证须记录原 owner 实际返回，可能是 attempt13。
不得截断/过滤后续历史，把当前全部历史的决策说成“attempt11 当时的回放”。
若另需 r38 时点回归，必须有独立可验证的历史投影；当前缺少时标 integration incomplete，
不与本轮 current-history / attempt11-source 的恢复验证混为一谈。

先检查 S01 是否已有 ProductionIntent、QA allocation、source-use observations 和合法 Registry
绑定。缺任何一项都必须在报告中保留；不能裸解析后 model_construct、补造 PASS，
或把 raw MP4 伪装成 activated Registry asset 来启动 resolver。

如果缺少 authoring/history projection，只允许提出一个 S01-specific 薄接线的后续 scope：
复用既有 schema 和 owner，保留原 requirements、proof 与 actor；不新增通用框架。
本 spec 不授权这项代码或 Project mutation。未完成真实输入接线时，只能报告
integration incomplete，不能把 synthetic fixture 通过当作 S01 workflow PASS。

### Candidate Comparison Without Predetermined Answer

至少逐项审查以下方案及其真实 blocker：

- unchanged reuse：保护原内容但不关闭手部 FAIL，不能冒充完整解决方案。
- preserve visual/audio + local hand repair：有 source/proof/assembly 资格才可执行；
  否则指出 localized edit、mask/tracking、输入或音轨入口的具体缺口。
- trim、fixed reframe、现有 composition：解释为什么能或不能满足时序、掌向和连续动态；
  禁止 speed-up + clone-tail objective substitution。
- full-generation：作为独立可比较的方案，依据真实失败历史和有效 intervention 评估，
  不能仅因用户不授权 submit 就声称模型不可用或策略不合适。
- split/cutaway：已有基本 materialization，但本 S01 被 single-take/co-visible 约束排除，
  不是 executor 不存在。

Capabilities 使用已配置 adapter 的只读静态观察，不做 remote discovery。
不得只用空 targets、generation_available=false 或关闭 exploration 获得预设 gap。
full-generation 对照不得被 local-edit unit 的 required_operations 污染；它应有独立完整
coverage/acceptance，且其 history/intervention 判断必须来自真正消费历史的既有 owner。

若当前 resolver 仍选择 full generation，必须原样记录，不由 driver 改写为 capability_gap。
若需要额外 history handoff 才能拒绝重复 intervention，则将它识别为 integration/decision
缺口。本轮零 submit 是安全边界，不是上述比较已经成功的证明。

### Actual Entry Points And Effects

验收必须记录实际调用的既有入口、输入/decision hash、候选清单与各 blocker，
而不是只输出 Agent 的自然语言结论。ProductionPlanningService.prepare /
reassess_generation 和既有 GenerationFeedback 入口只按其真实前置条件调用；
不能用伪造 SimpleNamespace decision 代替正式历史反馈链。

本轮未来回归运行限定零 Provider submit、零上传、零 render/媒体派生、零旧项目 mutation。
读取本地历史媒体/hash/probe 是观察，不是重新生成或新的人类观看证据。
执行边界用调用计数/拒绝证据验证，而不把 hard-coded no-submit 当成决策正确性的证明。

无 selected candidate 或仍有 gap 时，不继续 materialize、prepare_generation、composition
或 activation。若获得合法可执行方案，本轮只验证其 owner handoff/前提，
实际媒体执行及 whole-shot revalidate 留待明确授权；不为“跑完整流程”而产生媒体。

### Capability-Gap Evidence

一个有效的局部能力缺口至少同时说明：

1. 要修的 exact requirement 和来源 attempt/proof，及必须保留的内容。
2. 需要的 operation、作用的时间/空间语义及输出用途。
3. 当前 source/admission、表达、选择、materialization、executor 或验收中究竟缺哪一环。
4. 当前源码/API 为什么不能执行；已有 edit/extend/trim 等路径为什么不适用。
5. 全部候选的真实返回，未执行 full generation 的历史/干预理由和零副作用证据。

这是现有 decision/report 的证据要求，不引入新的持久化 gap schema、Gate 或 state owner。
缺少 source proof 要返回 evidence_required；仅因没有手部空间 schema 应标表达缺口；
只有支持“需局部编辑但当前 executor 不可用”的证据完整，才能得出相应 executor gap。

## Acceptance

| Outcome | Criteria | What It Does Not Prove |
| --- | --- | --- |
| Workflow regression PASS — justified gap | 真实 S01 输入/历史接线已验证；准确保留 PASS/FAIL/未知项和责任分配；实际入口评估候选；局部缺口可归因；重复 full-generation 未被选择或已由原 owner 以真实理由否决；零 submit、无 acceptance 漂白 | 不证明局部修复已执行、S01 完成、成片通过率或成本改善幅度 |
| Workflow regression PASS — executable handoff | 同上，且某个非整镜方案的输入资格、既有 materialization/execution/QA handoff 可执行性得到验证 | 尚未生成/组合的新媒体不能标质量 PASS |
| Integration incomplete | S01 无合格 intent/allocation/source binding/history caller，或仅有 synthetic fixture/static enum 证明 | 不能宣布第一轮真实 workflow 已通过 |
| Evidence required | 用途、掌向/腕部解释、音轨或其他必要 proof 无法判定 | 不是 executor gap，也不是 Shot PASS |
| Workflow regression FAIL | 仍默认重复 full generation、编造 reuse/source PASS、隐藏 blocker、污染对照、把全局冻结当修复，或仅因禁用 Provider 就断言策略成功 | 不能靠新的文档或 Gate 名称改成通过 |
| Recovery/authorization stop | 当前状态 unknown 或操作超出 scope；保留原 typed stop | 安全停机可以正确，但单独不足以证明 editorial decision 成功 |

本轮 PASS 最多标注“S01 历史真实案例的 decision-path regression 通过”，不称
“新的媒体修复能力通过”。所有 source PASS 只在原 identity/use 有效。
后续任何新 MP4/重组合都必须重新经过完整 frozen QA、exact-byte video-analysis、
必要的 1.0x 人类观看及 Final-output-first / No-regression；不得沿用旧片 PASS。

## Focused Controls

未来执行 regression 时至少验证：

- 配置完整的独立 full-generation 对照存在，真正重复 intervention 被原 history owner 识别；
  不以总失败次数直接推导模型不可能或可比 cohort。
- 合法且已合格的 supported reuse 对照仍可 selected，证明系统不是一律返回 gap。
- 移除/错绑 source proof 或混用 attempt11/12 hash 必须 evidence_required/typed reject；
  不错误转成 localized executor gap。
- 同时可见的“手+背景”不得被偷偷改成两个 sequential units；完整 requirement 无遗漏。
- 输出包含具体候选和准确 blocker；materialize/Provider/render/activation 零越权调用。
- 原 attempt FAIL、human proof、budget/quota/reservations、active pointers 不变。

这些控制应由最小测试/driver 和现有 contracts 承载，不是新增测试框架。
当前 source/test 只能证明部分原语；实际未跑的 S01 接线验证必须标未运行。

## Sequence And Deferred Work

顺序固定为：

S01 failure-recovery decision regression → 确认其 scoped PASS → S02 fresh-shot strategy validation。

S02 用于检验初次 authoring 是否正确分配复杂意图，而不是继续复制 one-shot generation。
S02 的独立 scope/输入/验收需另行确定；S01 integration incomplete 不自动推进 S02，
S01 成片仍未完成的事实也不妨碍在用户确认 decision regression 结果后讨论 S02。

原 /0.1 的单次 Provider-native VIDEO_EDIT 媒体实验移为后续候选，未选择 Provider，
没有一次 POST 的隐含授权。现有 failed-source lease、Ark asset materialization、音轨
VALIDATE/SETTLED/目标版本限制继续有效，详见
[generated-video audio](../../generated-video-audio.md)、
[Seedance asset](../../../src/ai_video/production/seedance_asset.py)。
不得假激活失败素材、假造 Ark Active、降级 schema 或新建 production direct-mux fallback。

## Non-Goals And Verification Boundary

不新增 NLE、Editorial Execution Layer、spatial component graph、mask/tracking 引擎、
Provider ranking、success estimate、taxonomy、更多 routing contracts 或通用 orchestration。
不修改 canonical ownership：ProductionStateCommitter 唯一 writer，ResolvedTimeline 唯一
timing，HyperFrames 默认 renderer，现有 QA/P6 独占验收。

本轮修订只做 source/record 对照、documentation checks 和独立 spec review。
未来若只缺一个 S01 输入/历史接线，先明确该最小 code/authoring scope 再实施；
若需要更大 schema/executor 变化，停止并报告，不以“完成 regression”为理由扩建架构。
