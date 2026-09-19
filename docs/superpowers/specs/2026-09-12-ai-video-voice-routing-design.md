---
surface_id: voice_source_routing
canonical: false
spec_status: proposed
implementation_status: in_progress
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: voice-routing/1
---

# AI-VIDEO Voice Source Routing Specification

## Status And Authority

Date: 2026-09-12。

最初以 docs-only 编写；用户随后要求“实现specs”，并确认在保留既有改动的基础上更新
共享 policy/matrix/baseline。当前实现处于 working-tree verification，尚未完成正式 closure。
本文仍为 proposed；代码与本轮验证结果优先，不由本文推导 live-ready 或 Provider 授权。
不修改 Production artifacts、历史 QA/verdict、S03 或 unknown attempts；不 commit/push，
不创建 worktree。实施授权不等于账户购买、付费执行、重新生成或质量验收授权。

## Implementation Binding

2026-09-13 修复：用户已确认相关 committer/models/policy ownership，保留并发任务既有内容。
`voice-routing-execution/1` envelope 将 exact route binding、实际 video preview 与 paid preview
封存在既有 voice attempt 的 `routing-binding.json`，由 receipt 的 paired task/hash 字段引用，
纳入 artifact hash 和标准 reader reopen。无字段的历史 receipt 保持原序列化与 exact replay。
既有 committer 在 R+1、R+2 与 paid intent 锁内重验当前 QA、lineage、readiness；paid owner
还核对 exact voice credential/currency/cost，并在当前 ledger 验证所选 voice + video 预算。
当前 task 的 voice/video submit 按 canonical evidence 合计去重，不计其他 task 或历史样本。
Routed voice submit 后增大已封存 task ceiling 当前明确阻断，不新增额度扩展 owner。
固定独立声线的 qualified positive evidence 已通过标准 loader/committer/ReviewReceipt 与
实际 Router 的离线测试；fixture 的 human receipt 不构成真实听感或 Provider 质量证明。
目前没有正式 Harness receipt，因此不构成全部 VR 验收通过；最终 review、实际验证与
剩余限制由 session record 和 runtime baseline 维护。

`Shot.voice_routing` 与 Planning projection 使用同一 `VoiceRoutingRequirement`；省略该字段时
旧序列化不增加 null/default 字段。`GenerationCandidate.voice_route` 枚举路线，现有 Router
唯一选择；完整 readiness 进入 exact binding，稳定质量比较范围不包含预算结算或待完成项。

`VoiceRoutingContext` 只声明实际所选既有 final project、exact `AudioTrackSpec`、voice request/
preview 与 Review pointers，不创建项目、不授权配音。新 voice execution 在既有 committer
调用前重新打开 source，检查视频能力、Graph/QA、当前 authoring、materializer、dependency
transition preparer、credential reference、账本与 unresolved attempts。SEPARATE 先经现有
`generate_voice_asset` 登记 `voice-{attempt_id}`，再从当前 Registry 重新 Planning/prepare 视频。
没有有效接线时明确阻断，不以孤立 WAV 或编译成功代替组合可执行性。

首版适配 Vidu compiler/3 与 Seedance compiler/2。独立 MiniMax voice request 保留旧语言
标签，boundary 仅显式映射 `en → English`、`zh → Chinese`；未验证变体阻断。原生 compiler
没有 exact fixed-speaker/reference control，因此跨镜头固定原生声线保持 EVIDENCE_REQUIRED。
独立固定声线只接收当前 QA authority 的 `voice-identity/1` human semantic evidence，重新
打开同布局中不同 canonical Shots 的真实 succeeded voice requests 与 generated asset provenance；
自报模型/voice_id、imported 音频或无关 Review 不构成资格。

P4 的可选 `CompositionSpec.voice_sources` 引用 source project 和既有 execution binding pointer；
历史空字段省略。新声音路线必须消费 exact selected fetched video、登记音频和封存 track。
首版不接受未经资格化的 speech trim/gain/fade/ducking；完整 speech 必须落在 canonical timeline
和已封存对白时间窗内。既有非本路线 P4 操作保持原契约。这是 read-only admission，不新增
timeline、Registry writer、direct mux 或 muted 绕过。

## Goal

在首次视频 submit 前，为当前 Shot 自动选择可执行的 voice source route，优先满足角色身份、
对白准确性、语言、音画同步和已认可内容保护等硬要求；仅在这些要求满足后优先使用模型原生声音。
禁止统一默认静音，也禁止把独立 TTS 或购买新 API 作为必经流程。

自动选择必须进入真实 Planning → candidate → Router → exact request 链，不能仅输出建议、
增加 config flag 或新增未被调用的 helper。每个选择都必须可解释、可重开、可验证。

## Current Evidence And Gap

以下是设计时的源码事实，不是未来能力承诺：

| Existing surface | Current behavior | Gap |
| --- | --- | --- |
| `planning/video_planner.py::build_provider_neutral_requirement()` | 传递 sealed projection 的 `audio_need`；REQUIRED 映射为需要 native audio | 没有“有对白但允许独立配音”的独立语义 |
| `production/generation_feedback.py::create_generation_candidates()` | 枚举已注册 Provider variants，沿用 target.output_requirement | 不枚举同一视频候选的不同 voice routes |
| `production/generation_decision.py` / `shot_router.py` | 验证和选择 exact candidates，封存选择结果 | 不评估跨镜头声线或 TTS 就绪条件 |
| `production/video_contracts.py` | `native_audio` 必填；capability 提供 `native_audio_options` | 有音轨能力不等于固定说话人能力 |
| `production/models.py::VoiceProfile` | `language`、`voice_hint`、`notes` | 文字描述不是可调用 voice identity，也不是一致性验收 |
| `production/vidu.py::_payload()` | `audio=effective_output.native_audio` | Adapter 不应承担选声策略 |
| `production/generated_video_audio.py` | 原生音频派生要求 exact settled source；target Manifest 当前仅支持 2.0–2.2 | 不能把生成有声视频等同于已能进入任何版本的最终成片 |

S03 历史 decision binding 的 `feature_scope.audio_need=forbidden`、八个候选的
`native_audio=false` 是上游封存策略，不是 Vidu 缺省关闭。此次设计不改写这些历史决定。
既有 [source-audio record](../../record_for_agent/2026-08-28-ecommerce-source-audio-gate-routing.md)
明确禁止统一“先静音、以后 P4 补音”；其 authoring/control-plane guidance 不等于 Product router。

## Scope

首版只覆盖新动态视频生成任务的逐 Shot voice route；候选来自已注册且在用户任务范围内的
视频 Provider，以及现有 MiniMax Speech 独立配音接入。不新增 Provider、模型或购买流程。
独立配音的实际执行仍由既有 voice request 与 `ProductionStateCommitter` 完成。

首版不实现跨角色自动选音色、音色克隆、自动声纹分析、LLM 自由打分、通用调度器、
背景音乐/SFX Provider router、stem separation 或新 lip-sync backend。
静态图文视频与其他 no-Video-Provider 路线继续使用既有 P4，不得因为本功能缺视频候选而退化。
已认可画面的后期补音不是新视频 submit 的理由；该场景保持既有后期路径，不能调用本 router 重生。

## Approaches And Decision

- Always native：流程简单，但没有固定音色/实验证据时不能承诺跨镜头一致。
- Always separate TTS：可显式固定音色，但增加独立依赖，且不能自动解决口型、情绪与时长。
- Constraint-first joint routing：推荐。按同一 Shot 的硬要求评估 video candidate × voice route，
  保留原生优先的次级偏好，不能以原生优先牺牲画面或声音要求。

“joint”只表示一起比较候选，不新增第二个全局 selector：最终选择仍由现有
`VideoGenerationResolver.resolve_requirement()` / generation decision owner 独占。

## Ownership And Integration

```text
Canonical Shot / Character / voice requirements / exact evidence
  → Planning sealed voice-routing input
  → existing candidate builder enumerates eligible video × voice routes
  → existing Router selects one exact route or returns a typed blocker
  → compiler + pre-submit checks verify the selected request
  → existing video and voice lifecycle owners execute permitted effects
  → registered audio → CompositionSpec → ResolvedTimeline → HyperFrames
```

- Planning 拥有需求投影；语音决策的纯规则可置于一个聚焦模块，不能创建新 Manager、服务或 lifecycle。
- `create_generation_candidates()` 枚举路线，不预选 Provider，也不替 Router 签发最终决定。
- 现有 Router 对 voice feasibility 做硬过滤，再使用既有视觉/生成适配排序；原生偏好只在
  其他硬要求均满足且既有排序无法区分的同等候选间生效。仍有歧义时保留现有显式歧义结果，
  不依赖遍历顺序、字符串 ID 或虚构成功概率破局。
- Provider adapter 仅验证/编译所选路线，不自行改 `native_audio`、换声线或选择 TTS。
- committer 继续独占 durable intent、permit、写入、activation 和 recovery。
- P4 继续独占最终音轨与时序；不移除 visual source 的 `muted`，不 direct mux。

## Input Contract

新增 sealed `voice-routing/1` 扩展，作为现有 Planning/requirement/decision 链的组成部分。
输入不得来自未验证的自由文本猜测或任意 caller 的 `qualified=true`：

| Concern | Required meaning |
| --- | --- |
| Identity | current Shot content hash、Character IDs/revisions、角色与台词段落的明确绑定、script hash、语言 |
| Intent | `AUTO`、`NATIVE_REQUIRED`、`SEPARATE_REQUIRED` 或明确 `NO_VOICE`；AUTO 是新功能的默认选择模式 |
| Consistency | `SINGLE_SHOT` 或 `CROSS_SHOT_FIXED`；角色的固定声线约束与参照来自 canonical authoring，不靠出现次数猜测 |
| Voice binding | 固定声线需求必须有 speaker identity 和 exact reference/voice identity；缺失返回 authoring/evidence gap |
| Synchronization | 是否可见发声、对白时间窗、口型/表演是否为硬要求；不把 offscreen narration 与 onscreen dialogue 混同 |
| Candidate capability | exact Provider/model/profile/compiler identity、音频支持、实际可表达的 voice control/reference binding |
| Readiness | 当前执行范围、credential reference 可用状态、已有 finite quotas、后期音频登记/合成和必要同步路径的适用性 |
| Evidence | exact output/reference hashes、适用角色/语言/模型/配方、验收 policy 与 findings、来源和有效范围 |

Metadata-only credential presence 只证明引用存在，不证明账户权限、额度或远程成功；router 不读取
secret、不探测余额、不调用 Provider，也不浏览价格。未知远程账户状态必须明确保留，不能伪造 live-ready。

独立配音候选必须绑定已有具体 voice/model/settings 与 endpoint/credential reference；只有
`voice_hint` 时不能自行挑选角色声线。多角色 Shot 必须逐角色满足约束；首版同 Shot 选择单一
对白来源路线，不支持一部分角色原生、一部分角色替换的混合 stem pipeline。

SEPARATE 的 readiness 必须验证既有执行布局：voice admission 拒绝同一 Manifest 内任意
RUNNING/OUTCOME_UNKNOWN，MiniMax count-based batch 与视频 monetary ledger 也不能混用。
不能仅因为两套 API 各自存在就宣称联合路径可用。所选同项目布局不满足顺序执行/账本约束，
或所选跨项目布局缺少 exact generated-voice 登记与组合 handoff 时，SEPARATE 返回
`BLOCKED_CAPABILITY`；只要求实际所选布局满足条件，不要求两类布局同时存在。
不得新建 root 规避原 unknown、把生成音频伪装成 imported，或把实验 WAV 路径当作 Production asset。
本 spec 不顺带授权实现新的跨项目音频导入子系统；缺口必须在决策中真实暴露。

## Voice Identity Evidence

区分三个层次：接口宣称支持控制、实际请求可绑定控制、针对目标声线的验收证据。
它们不能互相替代：

- `SINGLE_SHOT` 没有固定声线约束时，原生候选无需跨镜头声纹证据，但仍需语言/对白/同步能力。
- `CROSS_SHOT_FIXED` 的任一路线都必须绑定同一角色 voice identity，并有覆盖目标用途的有效
  一致性验收证据；固定 TTS `voice_id` 也不能自动当作所有情绪/语言下的一致性保证。
- 原生候选可以依赖已实现的固定 voice/reference 控制及其验证证据，或已有 exact 范围的
  跨镜头实验验收；不能仅依赖同一模型、相同 seed、相似提示词或 marketing claim。
- 只有单镜头成功、过期/不匹配证据、required finding NOT_EVALUATED 均不满足固定声线要求。
- 无证据时返回 `EVIDENCE_REQUIRED`。可报告最小建议实验，但不得为填补证据自动产生付费批次，
  也不得将探索输出标记为 Production qualified。沿用现有 QA/evidence owner，不建新的评分系统。

## Decision Contract

按下列顺序处理，显式用户约束优先于默认偏好：

1. 重验 exact input identity、当前 authoring、历史 attempt 与既有执行限制。
2. 若已经提交或存在 unknown，则进入既有停止/recovery规则，不重新计算并执行替代路线。
3. `NO_VOICE` 只表示不生成对白/旁白；不自动消除已声明的环境声、音乐或音效要求。
4. 为每个实际注册视频 capability 枚举允许的 native/separate route，过滤硬约束冲突。
5. 检查每个 route 的声线证据、语言、同步与到最终成片的能力链。
6. 由既有 Router 选择；无可用候选时输出 typed blocker 和最小 next owner，不静音降级。

| Condition | Result |
| --- | --- |
| AUTO，原生满足硬要求且在可行候选中不劣于已有排序结果 | NATIVE |
| AUTO，原生不满足要求，独立配音满足全部硬要求 | SEPARATE |
| AUTO，独立配音也缺声线/凭证/同步/合成能力 | BLOCKED，列明原因 |
| NATIVE_REQUIRED 但原生不可用 | BLOCKED；禁止改走 TTS |
| SEPARATE_REQUIRED 但配音不可用 | BLOCKED；禁止改走原生 |
| 跨镜头固定声线，两个路线都缺合格证据 | EVIDENCE_REQUIRED；不得假定 TTS 天然合格 |
| 相同候选其余条件相等，两条声音路线均合格 | NATIVE，记录偏好原因 |

对已明确 `NATIVE_REQUIRED` 或已接受 SourceAudioPolicy 的新任务，AUTO 不得覆盖其语义。
对于当前 S03 等历史 FORBIDDEN 策略，必须通过显式 prospective authoring revision 才能用于
未来不同目标，不能把旧记录重新解释为 AUTO。

## Output And Execution Binding

决策输出至少包含：`route`、逐角色 binding、exact selected video candidate identity、
独立配音配置引用（仅 SEPARATE）、policy/input/evidence hashes、拒绝其他路线的 reason codes，
以及 remaining execution/quality requirements。NO_VOICE 与 BLOCKED 不得伪装成静音成功。

所有候选按 Provider capability × voice route 拥有唯一 identity，保持 user-fixed Provider 约束，
不能因同一 capability 的两条路线而触发 duplicate IDs，也不能以此扩张 authorized candidate 集合。
Route/settings/evidence 改变必须改变 candidate scope/decision/binding hashes，并重新验证封存链。

NATIVE 候选输出 `native_audio=true`。SEPARATE 的对白生成要求只交给 voice owner，不发给
视频模型要求它再次生成对白。首版 SEPARATE 始终使用 `native_audio=false`，非对白音频由显式
P4 coverage 覆盖；若硬要求必须使用视频模型原生环境声/音效，则该 SEPARATE 候选返回范围冲突，
即使某 adapter 能只生成环境声，也不在首版启用混合路线。不得承诺后期自动分轨。
Canonical dialogue 保留，改变的只是各生成组件的责任投影，不能删除最终验收要求。

Selected route 必须由现有 pre-submit seam 与 compiler/permit 再验，不能只在 UI/日志显示。
独立 TTS 与视频使用各自既有 exact request、intent、quota 与 one-use permit；route decision
不是共用 permit，也不产生第二账本。首版只约束合法 handoff 与真实 entry wiring，不新增
跨服务事务协调器；执行顺序由既有 application caller 管理，并分别保留每个 effect 的状态。

任一执行 unknown 时停止当前组合，禁止切 route、remint、自动重试或以新 root 清空历史。
已完成的一个组件必须重用其 exact evidence，不因另一组件失败而重放。已知失败后也不得
由 router 自行开启替代调用；后续仍需既有 bounded repair/recovery owner。

## Compatibility And Migration

- 不改变历史 `AudioNeed.REQUIRED` 等于 native-required 的含义。新 voice requirement 与
  legacy audio_need 同时存在时必须一致，否则 fail closed；不能把 native-required 静默翻译成 TTS。
- 新扩展的 AUTO 投影使用 `audio_need=OPTIONAL` 表示原生音轨可选，并由独立 voice requirement
  强制最终对白必需；它不表示对白可以缺失。NATIVE_REQUIRED 映射 REQUIRED；仅独立配音且
  无原生非对白音频需求时映射 FORBIDDEN。Candidate-specific compiler projection 只能按已选
  route 分配对白责任，保留原 canonical intent/hash 和最终 requirement 引用，不能覆写原 requirement。
- 新扩展使用显式 `voice-routing/1` discriminator。缺失扩展的历史 request/plan/receipt 按旧语义
  exact reopen，序列化不得补默认字段导致旧 hash 变化。
- 新 AUTO 任务必须带完整扩展；Planner verifier、candidate scope、decision 与 execution binding
  同时绑定，删掉扩展不能作为绕过新 gate 的兼容入口。旧路径只承接显式 legacy任务，不能推导 AUTO。
- 不修改历史 Manifest、request、receipt、QA 或已接受媒体。新 authoring revision 只精确失效
  受影响的未来 voice/video request 与组合，不传播到无关 Shot。
- Runtime implementation 同步 canonical contract matrix、policy routing 与 baseline；用户已确认
  保留它们既有 staged changes 后追加本任务内容，不把 proposed spec 当作已验证 runtime。

## Acceptance Criteria

| ID | Executable acceptance |
| --- | --- |
| VR-01 | 从真实 Planning/candidate/Router entry 输入 AUTO，得到 route-bound compiled request；不存在只测纯 helper 的完成声明 |
| VR-02 | 原生支持且不要求固定声线时，在同等候选间选择 NATIVE；真实 adapter payload audio=true |
| VR-03 | 固定声线需求且原生缺证据、独立音色有合格证据时选择 SEPARATE；视频 payload 不重复生成对白，voice handoff 保留原文/角色/语言 |
| VR-04 | 两条路线都缺必要证据或适用执行能力时明确阻断，零 Provider/secret lookup/Manifest write |
| VR-05 | 固定模型/原生/独立选择等用户约束不被默认偏好覆盖；视觉硬要求优先，不能为了声音换成不合格画面候选 |
| VR-06 | 变更 speaker/reference/profile/evidence/region/route 会改变 identity；篡改、过期证据与跨候选复用 permit 在 transport 前拒绝 |
| VR-07 | 同一 Provider capability 的不同 routes 可合法枚举，无 duplicate ID，且不扩张原 finite quota/授权 Provider 范围 |
| VR-08 | 已认可画面不重新生成；旧 request/plan/receipt byte/hash exact reopen；新 AUTO 不可剥离扩展降级成 legacy |
| VR-09 | known failure 与 unknown 分开；unknown 不切换路线；部分完成后 exact reopen 不重复任何已完成副作用 |
| VR-10 | NATIVE stream 存在不等于 final audio ready；不兼容的登记/合成路径返回能力缺口，不移除 muted 或 direct mux |
| VR-11 | onscreen dialogue 的独立配音缺必要同步路径时阻断；NO_VOICE 不抹掉 ambience/SFX/BGM coverage；多角色逐一验证 |
| VR-12 | no-Video-Provider/P4、现有明确 native-required、视频付费 guard 与历史 MiniMax Speech 批次行为无回归 |
| VR-13 | SEPARATE 缺少兼容账本/顺序或exact generated-voice登记handoff时在任何submit前阻断；测试不得用独立实验WAV冒充跨项目接线完成 |

Focused suites 包括 `test_production_generation_decision.py`、`test_production_shot_router.py`、
`test_planning_video_planner.py`、`test_shot_readiness_gate.py`、`test_production_planning_generation.py`、
`test_production_vidu.py`、`test_production_minimax_speech*.py`、voice lifecycle 与 generated-audio suites。
实现新增的 route-specific 测试必须接入 Harness policy；按 semantic risk 使用 native reviewer_xhigh。
完整完成证据按当前 `.agent/harness/policy.yaml` 的真实 changed-path routing 执行。

## Verification Layers And Non-Goals

离线 tests 证明路由、绑定、拒绝与兼容，不证明真实声线一致、口型自然或账户可用。
独立 live proof 必须按 task scope、有界调用、实际记录和逐 Shot Gate 执行；本 spec 不授权 live。
固定声线的最终验收需要实际跨镜头试听及适用 evidence，不能被 selector confidence 取代。

不以 router 为理由自动购买服务、替用户配置金额预算、放宽 secret/permit/unknown gates、
重生 S03、推进 S04，或把历史 QA 的 NOT_EVALUATED 改成 PASS。

## Review Boundary

用户已要求进入 implementation；当前不另写微步骤计划。实现仍须完成独立 review 与实际验证。
实现必须交付实际入口行为、exact binding 与相应 tests，不能把“spec 已写”或“router 返回选择”
描述成语音已生成或成片已验收。
