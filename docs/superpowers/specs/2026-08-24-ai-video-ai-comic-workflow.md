# AI-VIDEO AI Comic Workflow Skill Specification

## Status

Proposed，documentation-only。本轮只授权创建本 spec 与配套 implementation plan；不授权创建或安装 Skill、修改 Product Runtime、调用 Provider、生成媒体、写 Production state、commit implementation、push 或 release。

本文定义独立的 `ai-comic-workflow`。它只服务 AI 漫剧 / AI 剧情短片创作，不承担电商广告、商品事实、广告 Hook、产品植入、CTA、campaign variant 或投放优化。现有 `Base AI Comic E2E` 继续是 Production Runtime 的 deterministic integration acceptance，不是本 Workflow 的替代品，也不是本 Workflow 的 durable state owner。

## Executive Decision

采用一个 repo-local、独立可触发的 `ai-comic-workflow`：

- 主定位为 **L2 Workflow Skill**；
- 只在既有 creative Skills 能提供明确 advisory value 时做薄 **L3 routing**；
- 不成为 Runtime，不生成媒体，不持久化 Production lifecycle；
- 输出一个独立 `AiComicProductionPackage`，再由 AI-VIDEO authoring / Production seam 显式 materialize 为现有 `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard` 与 `Shot`；
- 不读取、调用、导入或依赖 `ecommerce-ad-workflow`；
- 不建立跨 Workflow schema、shared orchestrator 或共同 creative state。

```text
AI Comic input
  -> ai-comic-workflow
  -> AiComicProductionPackage
  -> explicit AI-VIDEO authoring handoff
  -> ProductionProject / Asset Registry / VideoPlanner / Providers
  -> CompositionSpec -> ResolvedTimeline -> HyperFrames
  -> P6 Review / Repair / Final Acceptance

Ecommerce advertising is not part of this flow.
```

## Problem Statement

AI-VIDEO 当前已拥有完整的低层 Production primitives，但没有一个面向完整 AI 漫剧的 authoring decision sequence：

- `Story` 能表达 `logline`、`synopsis` 与 ordered beats；
- `Character` 能表达 identity、appearance、wardrobe、voice 与 reference assets；
- `Scene` 能表达 location、time、mood、participants 与 continuity constraints；
- `Storyboard` 能把 narrative beat 绑定到 Scene 与 Shot；
- `Shot` 能表达 intent、dialogue、narration、duration、characters、continuity、visual strategy、assets、motion 与 review policy；
- `VideoPlanner` 只对一个已存在的 target Shot 进行 generation / continuity / asset readiness preflight；
- `ResolvedTimeline`、HyperFrames、P4 audio/captions 与 P6 review 负责执行和证据，不决定故事。

因此当前缺口不是第二套 Runtime，而是位于 creative intent 与 canonical Production artifacts 之间的 AI 漫剧 Workflow contract。没有这一层时，Agent 容易直接写逐 Shot prompt，导致人物关系、情绪弧、场景状态、对白目的、镜头因果与集尾 payoff 只存在于散乱 prose 中。

## Goal

给定一个 AI 漫剧创作 brief，Workflow 必须按确定的 decision sequence 形成可审查、可机器验证、可交给现有 AI-VIDEO Runtime 的 `AiComicProductionPackage`：

```text
Premise / Genre / Audience
  -> Story Core
  -> Narrative Arc / Episode Beats
  -> Character Bible
  -> Relationship And State Model
  -> Scene Bible
  -> Dialogue / Voice Intent
  -> Storyboard
  -> Shot Intents
  -> Continuity Requirements
  -> Audio Intents
  -> Runtime Handoff
  -> AI Comic Logic QC
```

V1 的完成标准是输出一个结构化生产包，不是生成最终视频。

## Scope

### In Scope

- AI 漫剧 premise、genre、tone、theme、target audience 与 platform constraints；
- single-episode 与 episodic / serial mode；
- story core、narrative arc、conflict、turn、payoff 与 optional cliffhanger；
- protagonist、supporting characters、relationships、motivation、state transitions；
- Character Bible 与 Scene Bible 的 authoring proposal；
- dialogue、narration、voice、music、ambience 与 SFX intent；
- storyboard、Shot intent、open/close state、continuity requirements；
- 每个 Shot 的 narrative purpose 与 production need，不选择 Provider；
- capability-aware runtime handoff 与 unresolved capability list；
- pre-handoff AI comic logic QC；
- progressive disclosure references 与 deterministic package validation。

### Out Of Scope

- 商品、SKU、商品页面、Product Truth、claims、受众 pain point、广告 angle、广告 Hook；
- product placement、benefit proof、CTA、brand end card、广告 typography、campaign variants；
- Meta / TikTok / Google ad account、投放、预算、ROAS 或 performance optimization；
- Provider/profile selection、credential、budget、permit、submit、poll、fetch、retry 或 recovery；
- image/video/voice/audio generation、FFmpeg stitching、render 或 final delivery；
- 新的 ProductionProject schema、Asset Registry、Manifest、Dependency Graph、timeline、renderer、writer 或 review lifecycle；
- 用 Workflow package 冒充 activated Project、P6 PASS、Final Acceptance 或 release truth。

## Workflow Independence Contract

`ai-comic-workflow` 与 `ecommerce-ad-workflow` 是两个不同产品入口，不是父子 Skill，也不是同一 orchestrator 的 mode。

| Boundary | `ai-comic-workflow` | `ecommerce-ad-workflow` |
| --- | --- | --- |
| Primary intent | 叙事与角色驱动的 AI 漫剧 | 商品销售与商业传播 |
| Required truth | story / character / scene truth | product / claim / audience truth |
| Primary arc | setup -> conflict -> turn -> payoff | hook -> value -> proof -> CTA |
| Canonical package | `AiComicProductionPackage` | `EcommerceAdProductionPackage` |
| Cross-call | Forbidden | Forbidden |
| Shared business schema | None | None |
| Shared lower layer | AI-VIDEO Production Runtime only | AI-VIDEO Production Runtime only |

即使电商广告包含人物或短情节，也不得路由到本 Workflow；即使 AI 漫剧出现道具，也不得因此引入商品广告 contract。两者只可以独立映射到相同的底层 `Character`、`Scene`、`Storyboard`、`Shot` 等 Runtime models。

## Layer And Ownership

### `ai-comic-workflow` Owns

- authoring decision order；
- AI comic input completeness；
- story core、episode arc、character relationships 与 scene state；
- dialogue purpose、emotional progression 与 Shot narrative intent；
- continuity intent 的完整性；
- `AiComicProductionPackage` schema 与 pre-handoff QC；
- 把 creative requirements 映射为 runtime handoff proposals。

### AI-VIDEO Runtime Owns

- canonical `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot` revisions；
- reference asset identity、Asset Registry 与 provenance；
- `VideoPlanner`、`ShotReadinessGate`、Shot Router 与 exact capability checks；
- image/video/voice Provider selection and execution；
- `CompositionSpec`、`ResolvedTimeline`、HyperFrames、audio mix 与 captions；
- Production lifecycle、activation、recovery、Review、Repair 与 Final Acceptance。

### Advisory Skills

- `hell-grind-aigc-skill`：只用于 semantic Shot state、open/close state 与 continuity reasoning；
- `higgsfield`：只在 semantic Shot 已稳定后提供 provider/model prompt adaptation advice；
- `video-shotcraft`：只提供 motion、camera、pacing、transition、SFX 与 visual QA ideas。

它们的输出必须回到 `AiComicProductionPackage`，不得创建平行 Character/Scene/Shot truth、Provider request、timeline、render 或 QA state。

## Input Contract

V1 输入 schema version 固定为 `ai-comic-workflow/input/1`。

| Field | Required | Contract |
| --- | ---: | --- |
| `schema_version` | Yes | Exact value `ai-comic-workflow/input/1` |
| `project.title` | Yes | 非空项目标题 |
| `premise` | Yes | 一句话可拍摄的故事前提 |
| `genre` | Yes | 单个 primary genre；subgenre 可选 |
| `target_audience` | Yes | 内容受众，不是广告投放受众 |
| `platform` | Yes | 交付平台及其内容限制 |
| `duration_seconds` | Yes | 正数；single episode 的目标总时长 |
| `aspect_ratio` | Yes | 例如 `9:16`、`16:9` |
| `language` | Yes | dialogue / narration 的 primary language |
| `visual_style` | Yes | 可观察的媒介、质感、色彩与镜头基调 |
| `episode_mode` | Yes | `standalone` 或 `serial` |
| `episode_context` | Conditional | `serial` 时必须含 episode index、prior state、open threads |
| `references` | No | 用户提供的 story、visual、character 或 pacing references |
| `constraints` | No | 内容、年龄分级、时长、资产、风格与禁止项 |

Forbidden input fields：`product_truth`、`sku`、`advertising_angle`、`product_placement`、`cta`、`campaign`、`creative_variant_matrix`。出现任一字段必须返回 typed validation failure，不得静默忽略。

## Output Contract

V1 输出 schema version 固定为 `ai-comic-workflow/package/1`。

### `AiComicProductionPackage`

| Field | Contract |
| --- | --- |
| `package_id` | 对 canonical package bytes 的 deterministic identity |
| `source_input_hash` | exact input identity |
| `comic_brief` | title、premise、genre、audience、platform、duration、aspect、language、style |
| `story_core` | theme、dramatic_question、stakes、tone、ending_promise |
| `narrative_arc` | ordered acts / movements，含 setup、conflict、turn、payoff |
| `episode_plan` | standalone closure 或 serial threads / cliffhanger contract |
| `characters` | identity、appearance、wardrobe、voice、motivation、relationships、allowed variations |
| `scenes` | location、time、mood、participants、visual anchors、continuity constraints |
| `story_beats` | ordered beat、purpose、character state before/after、scene、duration budget |
| `dialogue_plan` | speaker、line intent、verbatim draft、subtext、delivery、lip-sync requirement |
| `storyboard` | beat-to-Shot grouping 与 narrative intent |
| `shot_intents` | Shot purpose、open/close state、action、camera intent、dialogue/narration、visual need |
| `continuity_requirements` | identity、wardrobe、prop、space、axis、action、light、environment、audio state |
| `audio_intents` | dialogue、narration、music、ambience、SFX 及 intentional silence |
| `runtime_handoff` | 对现有 Production artifacts 的 proposal 与 capability requirements |
| `qc_report` | deterministic pre-handoff findings；不等于 P6 verdict |
| `unresolved_items` | 必须由 human 或 Runtime gate 解决的 exact items |

### Runtime Handoff Projection

`runtime_handoff` 只允许 proposal，不允许 durable pointers 或 execution state：

| Workflow output | Existing AI-VIDEO target |
| --- | --- |
| `comic_brief` | `ProductionBrief` proposal |
| `story_core` + `story_beats` | `Story` / `StoryBeat` proposal |
| `characters` | `Character` proposal |
| `scenes` | `Scene` proposal |
| `storyboard` | `Storyboard` / `StoryboardBeat` proposal |
| `shot_intents` | `Shot` proposal |
| `continuity_requirements` | `Shot.continuity_constraints` and planning evidence proposal |
| `audio_intents` | future `AudioTrackSpec` authoring request；timing仍由 `ResolvedTimeline` 决定 |
| spoken dialogue captions | `CaptionTrack` request；只表示对白/旁白字幕 |

Forbidden output fields：Provider name/profile、credential、budget permit、task ID、Manifest revision、Registry activation、timeline frames/samples、render path、Review PASS、Final Acceptance。

## Workflow State Machine

```text
INPUT
  -> G0 INPUT_READY
  -> G1 STORY_CORE_APPROVED
  -> G2 CHARACTER_SCENE_BIBLE_COHERENT
  -> G3 BEAT_ARC_CLOSED
  -> G4 STORYBOARD_SHOTS_TRACEABLE
  -> G5 CONTINUITY_AUDIO_COMPLETE
  -> G6 RUNTIME_HANDOFF_VALID
  -> G7 AI_COMIC_QC_PASS
  -> PACKAGE_READY
```

### Gate Semantics

- **G0**：required fields complete；forbidden advertising fields absent；references readable or explicitly unavailable。
- **G1**：dramatic question、stakes、turn 与 ending promise互不矛盾。
- **G2**：每个角色和场景有 stable identity anchors；relationships 与 participant references有效。
- **G3**：每个 beat 有 narrative purpose、state change 与 duration budget；standalone 必须 closure，serial 必须标记 retained threads。
- **G4**：每个 beat 映射至少一个 Shot；每个 Shot 反向追溯到一个 beat，不允许孤立 montage filler。
- **G5**：相邻 Shot 的 open/close state可衔接；dialogue、narration、music、ambience、SFX 与 intentional silence有明确覆盖。
- **G6**：handoff 只使用 existing runtime concepts或明确列出 capability gap；不伪造 unsupported capability。
- **G7**：logic QC无 blocking finding；human taste、media quality 与 P6 acceptance仍未评估。

任何 gate 失败都必须停止在当前 authoring stage，输出 exact diagnostic；不得通过选择 Provider、生成占位媒体或降低 continuity requirement 自动继续。

## AI Comic QC Contract

V1 pre-handoff QC 至少检查：

1. premise、dramatic question、stakes 与 payoff 可互相追溯；
2. protagonist 在每个主要 beat 的目标和状态变化明确；
3. 每个 supporting character 有叙事功能，不是随机重置人物；
4. Character / Scene / prop identity anchors 在 Shot 中保持引用；
5. beat 与 Shot 不是固定时长机械切片；
6. dialogue 推动冲突、关系或信息，不是重复画面；
7. serial cliffhanger 不替代本集最低限度 payoff；
8. 所有 required dialogue 有 audio intent 与 lip-sync requirement；
9. silence 必须显式 `intentional`，不能由缺轨造成；
10. runtime capability gap 被诚实列出，不被 prose 隐藏。

## Skill Package Architecture

推荐使用一个 Skill 加按需 references，不拆成多个可触发微 Skill：

```text
.agents/skills/ai-comic-workflow/
├── SKILL.md
├── references/
│   ├── story-core-and-arcs.md
│   ├── episodic-structure.md
│   ├── character-and-relationships.md
│   ├── scene-and-state-continuity.md
│   ├── dialogue-and-audio.md
│   ├── storyboard-and-shot-intent.md
│   ├── runtime-handoff.md
│   └── ai-comic-qc.md
├── schemas/
│   ├── ai-comic-input.schema.json
│   └── ai-comic-production-package.schema.json
├── templates/
│   ├── standalone-vertical-short.input.example.json
│   ├── standalone-vertical-short.package.example.json
│   ├── serial-vertical-short.input.example.json
│   └── serial-vertical-short.package.example.json
└── scripts/
    └── validate_contract.py
```

`SKILL.md` 只保留触发条件、decision sequence、gate、reference routing 与 output rule；长篇方法论按阶段读取。V1 不创建 `ad-story`、`character-bible`、`shot-plan` 等平级 Skill，避免 trigger collision 与第二 lifecycle owner。

## Compatibility And Failure Behavior

- 不修改 public CLI、Production schema、Manifest、Registry 或 artifact layout；
- 不新增 runtime dependency；validator 使用当前 Python environment 可用能力且保持 no-network/no-write；
- package schema 是 Skill authoring artifact，不登记为 implemented Production surface；
- Runtime materialization 必须显式完成，不能因为 package valid 就自动写 state；
- input/output schema drift 必须 bump contract version，旧 example 继续可验证或显式拒绝；
- validator、Skill 或 reference 缺失时 fail closed，不自动 fallback 到 `open-video`；
- rollback 为移除该 Skill package、tests 与 routing，不触碰 Production artifacts。

## Acceptance Criteria

1. `.agents/skills/ai-comic-workflow/SKILL.md` 可被 Codex discovery，且触发描述只覆盖 AI 漫剧 / episodic fiction。
2. Skill 明确拒绝 ecommerce / product / ad / CTA / campaign input，不调用 `ecommerce-ad-workflow`。
3. Valid standalone input 产生 schema-valid `AiComicProductionPackage`，所有 Shot 可追溯到 story beat。
4. Valid serial input包含 prior state、retained threads 与 cliffhanger，但不要求广告字段。
5. Character、Scene、Storyboard、Shot references 的 dangling ID 被 validator拒绝。
6. 相邻 Shot 缺 open/close state、dialogue 缺 audio intent、非 intentional audio gap 均阻止 `PACKAGE_READY`。
7. `runtime_handoff` 不含 Provider、credential、permit、Manifest、timeline、render、P6 或 activation fields。
8. Existing `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot` owner不变。
9. Existing `ResolvedTimeline`、HyperFrames、`ProductionStateCommitter`、P6 owner不变。
10. No network、no Provider、no media generation、no Production write 的 contract tests通过。
11. Harness 对 exact Skill/test/control-plane delta运行 mandatory checks并产生 fresh receipt。
12. 文档与 tests 不把 package validity声称为 media quality、P6 PASS、Final Acceptance 或 release。

## Verification Strategy

Implementation 时至少提供：

- schema / validator unit tests；
- valid standalone 与 serial fixtures；
- forbidden advertising fields tests；
- reference-integrity、continuity、audio-coverage 与 runtime-handoff forbidden-field tests；
- Codex Skill discovery / progressive-disclosure static checks；
- Harness routing tests；
- exact staged snapshot verification。

任何 live Provider、ComfyUI、media、lip-sync、continuity quality 或 human acceptance 都不属于本 Skill V1 的 verification。

## Repository Evidence

- `src/ai_video/production/models.py`：`ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot`、`AudioTrackSpec`、`CaptionTrack`、`CompositionSpec`、`ResolvedTimeline`；
- `src/ai_video/planning/video_planner.py`：single-Shot `VideoPlanner` 与 current-plan consumer；
- `src/ai_video/production/state_commit.py`：唯一 Production writer；
- `src/ai_video/production/composition.py`：canonical composition resolution；
- `src/ai_video/production/hyperframes.py`：默认 Production renderer adapter；
- `docs/superpowers/specs/2026-08-18-ai-video-base-ai-comic-e2e.md`：现有 deterministic Runtime acceptance；
- `docs/superpowers/specs/2026-08-21-ai-video-video-planner-subagent.md`：per-Shot planning boundary；
- `AGENTS.md`：Creative Skill routing、single-writer、single-timeline、Provider 与 acceptance invariants。

## Final Boundary

`ai-comic-workflow` 的唯一产品价值是把 AI 漫剧的创作决策变成结构化、可验证的 authoring package。它不做广告，不调用广告 Workflow，也不成为媒体生产系统。
