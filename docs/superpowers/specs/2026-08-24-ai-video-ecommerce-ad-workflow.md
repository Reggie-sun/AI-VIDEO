# AI-VIDEO Ecommerce Advertising Workflow Skill Specification

## Status

`ecommerce-ad-workflow/1` authoring contract 已进入 current local implementation，并保持 offline Development / authoring boundary。本文新增的 `AdCreativePlan` Runtime bridge 仍为 **Proposed / not implemented**；它不授权修改 Product Runtime、调用 Provider、生成媒体、读取 credential、付费、写 Production state、push 或 release。

本文定义独立的 `ecommerce-ad-workflow`。它只服务电商商品广告，不承担 AI 漫剧、episodic fiction、Character-driven serial drama 或 cliffhanger production。此前把“AI 漫剧广告”作为该 Workflow 核心形态的方向被本文明确否决：AI 漫剧与电商广告必须是两条独立 Workflow，互不调用、互不依赖、没有共享上层业务 schema。

## Executive Decision

采用一个 repo-local `ecommerce-ad-workflow`，自建 contract 并选择性吸收外部广告方法论：

- 主定位为 **L2 Workflow Skill**，只做广告决策顺序与交付合同；
- 允许薄 **L3 advisory routing**，但不创建 Agent runtime、campaign runtime 或媒体 Runtime；
- 不直接安装、fork、vendor、submodule 或依赖 `aiads-skills`、`awesome-ai-video-workflows`、`claude-ads`；
- V1 输出独立 `EcommerceAdProductionPackage`；
- AI-VIDEO Runtime继续拥有 canonical assets、Shot readiness、Provider、timeline、render、audio/captions、Review/Repair 与 Final Acceptance；
- 不调用、导入或复用 `ai-comic-workflow` 的 schema、references、templates 或 outputs。

```text
Product / SKU input
  -> ecommerce-ad-workflow
  -> EcommerceAdProductionPackage
  -> explicit AI-VIDEO authoring handoff
  -> ProductionProject / Asset Registry / VideoPlanner / Providers
  -> CompositionSpec -> ResolvedTimeline -> HyperFrames
  -> P6 Review / Repair / Final Acceptance

AI comic authoring is not part of this flow.
```

## Problem Statement

AI-VIDEO 当前能生成和组合媒体，但没有结构化表达电商广告的上层语义：

- `ProductionBrief` 是通用 brief，没有 SKU、Product Truth、claim ledger、platform objective 或 CTA；
- `Story` / `Storyboard` / `Shot` 可以承接序列与镜头，但没有 hook、benefit、proof、product reveal、hero shot 或 brand closure role；
- `VideoPlanner` 是 per-Shot generation / continuity readiness planner，不是全片广告 Director；
- `CompositionLayerSpec` 主要表达 asset、trim、fixed transform、opacity 与 z-index，没有 Product Placement / Product Reveal / Product Interaction semantics；
- `CaptionTrack` 绑定 speech audio、transcript、alignment 与基础 style identity，是 dialogue / accessibility caption contract，不是 Commercial Advertising Typography；
- P4 有 audio tracks、gain、fade 与 ducking，但没有广告 cue、reveal hit、beat coverage 或 intentional-silence plan；
- P6 有 technical/layout/strategy/semantic lifecycle，但没有 product truth、product integration、advertising typography、CTA 与 brand closure rubric。

这些缺口会系统性地产生：产品突然出现、PNG 贴纸感、字幕模板感、产品名缺失、镜头与文案不同步、中段音频空洞、机械 cut、缺少 hero shot 与品牌收束。V1 Workflow 必须先解决广告 decision semantics，并对 Runtime尚不能表达的部分诚实 fail closed；不得通过 prose 假装底层已经具备 compositing 或 motion-graphics capability。

## Goal

给定商品资料、目标消费者与广告约束，Workflow 必须按广告逻辑形成可审查、可机器验证、可交给现有 AI-VIDEO Runtime 的 `EcommerceAdProductionPackage`：

```text
Product Truth
  -> Audience / Pain Point
  -> Advertising Angle
  -> Hook Contract
  -> Ad Beat Sequence
  -> Product Presentation Strategy
  -> Talent / Set Plan
  -> Copy And Advertising Graphics Roles
  -> Audio Emphasis And Coverage
  -> Storyboard / Shot Intents
  -> CTA / Brand Closure
  -> Creative Variant Matrix
  -> Runtime Handoff
  -> Ad Logic QC
```

V1 的完成标准是输出一个 30 秒竖屏电商广告生产包，不是生成最终广告。

## Scope

### In Scope

- SKU / product identity、source assets、landing page facts 与 rights references；
- verified facts、allowed claims、prohibited claims、required disclaimers；
- audience、pain point、desired outcome、platform 与 advertising objective；
- advertising angle、promise、proof boundary 与 objection handling；
- structured visual / dialogue / audio / copy Hook；
- ad beat sequence、duration budget、product introduction、demonstration、payoff、hero shot、CTA；
- product presentation mode 与 product-source identity constraints；
- presenter / talent、location / set 与 wardrobe 的 ad-specific plan；
- dialogue、voice-over、music、SFX、audio emphasis 与 intentional silence；
- advertising copy roles，与 dialogue subtitles严格区分；
- storyboard、Shot intent、product visibility 与 copy/audio synchronization；
- one-variable-at-a-time creative variant matrix；
- capability-aware runtime handoff 与 ad-logic preflight QC。

### Supported V1 Ad Formats

- `product_demo`；
- `presenter_spokesperson`；
- `lifestyle_use_case`；
- `comparison`，仅在 Product Truth 和平台规则允许时；
- `problem_solution`；
- `motion_graphics_product`，仅作为 desired creative intent，Runtime capability必须另行验证。

### Out Of Scope

- AI 漫剧、serial drama、episode、cliffhanger、fictional world bible；
- 调用或依赖 `ai-comic-workflow`；
- 虚构 testimonial、伪造认证、未经证实的 before/after 或任何医疗 / 治疗效果表达；
- Meta / Google / TikTok ad account、campaign publishing、budget、ROAS、attribution 或自动优化；
- Provider/profile selection、credential、permit、submit、poll、fetch、retry 或 recovery；
- image/video/audio generation、render、stitch、delivery；
- static image delivery；商品图片只可作为 source/reference asset，V1 目标交付介质始终是 video；
- 新 timeline、renderer、writer、Asset Registry、Manifest、Dependency Graph 或 QA lifecycle；
- 把 ad-logic QC 视为 P6 PASS、Final Acceptance 或投放效果证据。

## Workflow Independence Contract

| Boundary | `ecommerce-ad-workflow` | `ai-comic-workflow` |
| --- | --- | --- |
| Primary intent | 商品销售与商业传播 | 叙事与角色驱动的 AI 漫剧 |
| Required truth | product / claim / audience truth | story / character / scene truth |
| Primary sequence | hook -> value -> proof -> CTA | setup -> conflict -> turn -> payoff |
| Human subject model | `talent_plan` | `character_bible` |
| Environment model | `set_plan` | `scene_bible` |
| Canonical package | `EcommerceAdProductionPackage` | `AiComicProductionPackage` |
| Cross-call | Forbidden | Forbidden |
| Shared lower layer | AI-VIDEO Production Runtime only | AI-VIDEO Production Runtime only |

广告可以包含人物、生活场景或简短 problem/solution progression，但这些内容仍由广告 Workflow 的 `talent_plan`、`set_plan` 与 `ad_beats` 表达；不得借此进入 AI 漫剧 Workflow 或共享 `character_bible` / `episode_plan`。

## Layer And Ownership

### `ecommerce-ad-workflow` Owns

- Product Truth completeness and claim constraints；
- audience、pain point、angle、promise、proof 与 CTA；
- Hook contract 与 ad beat sequence；
- product presentation / reveal / demo / hero-shot intent；
- advertising copy role、visual hierarchy intent 与 synchronized cue；
- audio emphasis / coverage intent；
- creative variant matrix；
- `EcommerceAdProductionPackage` schema 与 pre-handoff Ad QC；
- Runtime capability needs 和 unsupported-gap reporting。

### AI-VIDEO Runtime Owns

- canonical `ProductionBrief`、talent-as-`Character`、set-as-`Scene`、`Storyboard`、`Shot` revisions；
- product source asset identity、rights/provenance、Registry、image import/generation；
- `VideoPlanner`、Shot readiness、continuity、Router 与 exact Provider capability；
- image/video/voice Provider execution；
- `CompositionSpec`、`ResolvedTimeline`、HyperFrames、audio mix 与 dialogue captions；
- Product state lifecycle、activation、Review、Repair 与 Final Acceptance。

### Advisory Skills

- `video-shotcraft`：可为 ad pacing、motion、transition、SFX 与 graphic treatment 提供 ideas；
- `hell-grind-aigc-skill`：只在广告 Shot 有人物 / 物体 state continuity 时提供 semantic continuity advice；
- `higgsfield`：只在 semantic Shot 与 exact Runtime policy已经确定后提供 provider prompt adaptation advice。

它们不得决定广告 truth、Provider selection、timeline、render 或 Production acceptance。

## Input Contract

V1 输入 schema version 固定为 `ecommerce-ad-workflow/input/1`。

| Field | Required | Contract |
| --- | ---: | --- |
| `schema_version` | Yes | Exact value `ecommerce-ad-workflow/input/1` |
| `product.sku_id` | Yes | 稳定 SKU identity |
| `product.name` | Yes | 广告必须可见或可听提及的正式商品名 |
| `product.source_assets` | Yes | 商品图片 / 视频的 exact references 与使用权状态 |
| `product.landing_page` | No | 用户提供的商品页 URL / snapshot reference；Workflow不自行抓取未授权页面 |
| `product_truth.facts` | Yes | 有 source 的 observable facts |
| `product_truth.allowed_claims` | Yes | 可使用 claim；每项绑定 fact/source |
| `product_truth.prohibited_claims` | Yes | 禁用、未证实、夸大边界；V1 必须包含全部医疗 / 治疗效果表达 |
| `product_truth.required_disclaimers` | No | 平台 / 法务要求 |
| `audience` | Yes | target consumer、context、pain point、desired outcome |
| `platform` | Yes | platform、placement 与 content constraints |
| `objective` | Yes | awareness、consideration、conversion 等明确目标 |
| `duration_seconds` | Yes | V1 target 为 30 秒；validator允许 spec 规定的 bounded range |
| `aspect_ratio` | Yes | V1 primary 为 `9:16` |
| `language` | Yes | copy / dialogue / VO primary language |
| `style` | Yes | 可观察的 commercial visual direction |
| `ad_format` | Yes | V1 supported format enum |
| `references` | No | reference ads、brand guides、visual / audio references |
| `constraints` | No | budget intent、rights、prohibited content、required mentions |

Forbidden input fields：`episode_mode`、`episode_context`、`cliffhanger`、`serial_arc`、`ai_comic_package`、`character_bible`。出现任一字段必须返回 typed validation failure。

## Output Contract

V1 输出 schema version 固定为 `ecommerce-ad-workflow/package/1`。

### `EcommerceAdProductionPackage`

| Field | Contract |
| --- | --- |
| `package_id` | canonical package bytes 的 deterministic identity |
| `source_input_hash` | exact input identity |
| `product_truth` | normalized facts、source refs、allowed/prohibited claims、disclaimers |
| `claim_ledger` | 每个 proposed claim 的 source、status、used_at、spoken/visual form |
| `ad_strategy` | audience、pain point、angle、promise、proof boundary、objective |
| `hook_contract` | visual、dialogue/VO、copy、audio、conflict/curiosity components |
| `ad_beats` | ordered beat role、message、duration budget、product/copy/audio expectations |
| `product_presentation` | intro、demo、payoff、hero-shot、physical-vs-graphic mode、source asset identity |
| `talent_plan` | presenter/user identity、appearance、wardrobe、performance、continuity anchors |
| `set_plan` | location、lighting、brand palette、product surface、continuity anchors |
| `copy_graphics_plan` | typed advertising copy roles、hierarchy、placement intent、cue binding |
| `audio_plan` | dialogue/VO/music/SFX events、coverage、emphasis、source-audio/lead-in policy、silence policy |
| `storyboard` | ad beat-to-Shot grouping，不表示 fiction episode |
| `shot_intents` | Shot purpose、product state、talent action、camera、copy/audio cue、visual strategy need |
| `cta` | spoken、visual、destination/action、end-card requirement |
| `creative_variant_matrix` | master truth、held constants、one changed variable per variant |
| `runtime_handoff` | current Runtime proposals、required capabilities、unsupported gaps |
| `ad_qc_report` | truth / logic / placement / typography / audio / closure findings |
| `unresolved_items` | human / legal / Runtime gate 必须解决的 exact items |

Forbidden output fields：episode、cliffhanger、serial thread、AI comic package reference、Provider name/profile、credential、permit、task ID、Manifest revision、timeline frames/samples、render path、P6 PASS、Final Acceptance。

## Product Presentation Contract

商品不得只被理解为“在某时间把 PNG 放到 `(x, y)`”。每次商品出现必须具有一个 typed purpose 与 mode：

### Presentation Roles

- `INTRO`：第一次建立商品 identity；
- `DEMONSTRATION`：展示可验证使用行为或 feature；
- `BENEFIT_PROOF`：只呈现 Product Truth 支持的结果；
- `HERO_SHOT`：受控、清晰、品牌化商品画面；
- `CTA_SUPPORT`：与 CTA / end card 同步。

### Presentation Modes

- `IN_SCENE_GENERATED`：商品必须在 source media 中被人物或场景自然承接；
- `GRAPHIC_REVEAL`：明确承认商品属于 graphic layer，以设计语言入场，不伪装成物理接触；
- `DEDICATED_HERO_SHOT`：独立商品镜头；
- `PHYSICAL_INTERACTION_REQUIRED`：要求手持、接触、遮挡、透视、shadow、tracking 等；若 current Runtime/source strategy不能满足，handoff 必须 `BLOCKED_CAPABILITY_GAP`。

每项 presentation 必须定义：beat、Shot、start intent、duration intent、role、mode、product source identity、talent interaction、occlusion need、lighting/shadow need、copy cue、audio cue 与 fallback policy。Fallback 只能切换为明确 graphic treatment或独立 hero shot，并需要重新批准 creative intent；不得把 static overlay 冒充 hand-held product。

## Advertising Copy Graphics Contract

商业图文不得全部映射为 `CaptionTrack`。V1 必须区分：

- `DIALOGUE_SUBTITLE`：对白 / 旁白的 audio-aligned subtitle，可映射现有 `CaptionTrack`；
- `HEADLINE`：Hook 或核心命题；
- `BENEFIT_CALLOUT`：卖点 / benefit 强调；
- `PRODUCT_LABEL`：商品名、型号或关键 identity；
- `PROOF_LABEL`：事实 / 参数 / disclaimer；
- `CTA`：行动文案；
- `BRAND_END_CARD`：品牌收束。

每个 graphic item 必须声明 role、text、priority、beat/Shot binding、safe-area intent、subject/product avoidance、entrance/exit intent、keyword emphasis、brand token reference 与 synchronized audio/product event。

`HEADLINE` 等 role 当前没有完整 Product Runtime expression surface时，`runtime_handoff` 必须记录 `required_capability=advertising_copy_graphics` 与 gap；不得降级成所有 Shot 共用的机械 Caption style 并声称完成。

## Audio Coverage Contract

V1 必须把“中段声音消失”作为 pre-handoff blocker，而不是 render 后才发现的偶然问题。

每个 ad beat 必须声明：

- dialogue / VO expectation；
- on-camera speaker、verbatim line 与 `lip_sync_required`；
- music presence、energy 与 transition；
- SFX / reveal hit / product interaction cue；
- generated/native source audio 的 `keep`、`mute`、`replace` 或 `trim_then_mix` policy；
- Shot opening noise / unwanted lead-in 的 trim、fade 与 P6 measurement requirement；
- intentional silence window；
- ducking requirement；
- source / generation need；
- cue 与 product/copy event 的同步关系。

`audio_plan.coverage` 必须覆盖完整广告时长。无 audio event 的 window 只有在 `intentional_silence=true` 且有 narrative/commercial rationale 时才合法。该 gate只验证 intent coverage；实际 audio asset、sample timing、mix、loudness 与 stream completeness仍由 P4、`ResolvedTimeline`、renderer 与 P6 验证。

## Hook Contract

Hook 不是单句 copy。`hook_contract` 至少包含：

- `visual_hook`；
- `dialogue_or_vo_hook`；
- `copy_hook`；
- `audio_hook`；
- `product_presence`：`none`、`tease` 或 `explicit`；
- `promise_boundary`；
- `first_payoff_deadline_seconds`；
- `platform_constraints`。

至少一个 component 必须在第一秒可观察；所有 promise 必须回到 claim ledger。任何医疗 / 治疗效果表达，以及没有证据的功能、before/after 或 absolute claim，必须被拒绝。

## Creative Variant Matrix

同一 `product_truth` 和 master strategy 下，V1 可以生成 variants，但每个 variant 只能改变一个 declared variable：

- Hook；
- opening visual；
- advertising angle；
- proof order；
- CTA；
- presenter profile；
- pacing；
- duration cut。

每个 variant 必须声明：`changed_variable`、`baseline_value`、`variant_value`、`held_constants`、`hypothesis` 与 `required_new_assets`。Provider retries、random seed changes、repair attempts 或不同 selected media 不得冒充 creative variant。

## Runtime Handoff Projection

| Workflow output | Existing AI-VIDEO target |
| --- | --- |
| `product_truth` / constraints | `ProductionBrief` proposal + upstream truth attachment；不得压缩掉 source/claim ledger |
| `talent_plan` | `Character` proposal when on-screen talent exists |
| `set_plan` | `Scene` proposal |
| `ad_beats` / `storyboard` | `Storyboard` / `StoryboardBeat` proposal |
| `shot_intents` | `Shot` proposal |
| product source assets | Registry import / image generation request through existing owner |
| product/talent continuity | `Shot.continuity_constraints` + planning evidence proposal |
| dialogue / VO | `AudioTrackSpec` authoring request |
| `DIALOGUE_SUBTITLE` | `CaptionTrack` / `CaptionTrackBinding` request |
| advertising graphics | explicit capability requirement；不得塞进 ordinary caption |
| audio cues | P4 authoring request；exact timing由 `ResolvedTimeline` 决定 |
| product presentation | visual/source/compositing requirements；exact feasibility由 Runtime gate决定 |

`runtime_handoff` 必须把需求分为：

- `SUPPORTED_CURRENTLY`；
- `REQUIRES_SOURCE_GENERATION_STRATEGY`；
- `REQUIRES_RUNTIME_CAPABILITY`；
- `REQUIRES_HUMAN_DECISION`；
- `BLOCKED_BY_TRUTH_OR_RIGHTS`。

Workflow 不得把 creative desire 自动翻译为 unsupported `CompositionSpec` 字段，也不得建立第二 renderer/timeline path。

## Proposed Runtime Follow-up: `AdCreativePlan`

### Decision

广告 Runtime 缺口不需要十个新 service，也不需要替换现有生产链。批准进入后续设计的最小集合只有一个 versioned `AdCreativePlan`，位于通用 brief 与 Shot planning 之间：

```text
ProductionBrief
  -> AdCreativePlan
  -> Shot proposals + typed product / graphic / sound treatments
  -> CompositionSpec
  -> ResolvedTimeline
  -> HyperFrames
```

`AdCreativePlan` 是广告语义的单一上层 contract，不是第二条 timeline、renderer、writer、Registry、Manifest 或 lifecycle。它只把已经通过 Product Truth / claim / rights gates 的广告意图编译到现有 Shot 与 composition path；exact frame/sample timing 继续只由 `ResolvedTimeline` 计算，durable mutation 继续只由 `ProductionStateCommitter` 执行，render selection 继续由 HyperFrames owner 决定。

### Minimal Contract

V1 最小字段为：

- `creative_concept`：全片唯一广告机制，不是每个 Shot 各自重新发明 concept；
- `protagonist_continuity_policy`：主角、montage mechanism、talent identity 与允许变化；
- `ad_arc`：typed beat roles，至少覆盖 problem / product introduction / demonstration-or-proof / payoff / hero / CTA / brand closure 中适用的节点；
- `product_presentations`：嵌套 typed `product_presentation`；
- `graphic_treatments`：嵌套 typed `graphic_treatment`；
- `sound_cues`：嵌套 typed advertising sound cue；
- `visual_motif`：跨 Shot 的品牌色、形状、节奏或 recurring device；
- `hero_shot`、`end_card` 与 `cta`：必须绑定 beat、Shot intent、商品 identity 与 claim boundary。

`product_presentation.mode` 至少区分：

- `IN_SCENE_PROVIDER`：商品属于 source generation；必须由 Provider/source evidence证明真实存在，不得用平面 PNG 冒充人物手持、接触或遮挡；
- `GRAPHIC_REVEAL`：商品明确属于商业 graphic layer，可使用受限 2D entry / position / scale / rotation / opacity / shadow / clip treatment，不伪装成物理融合；
- `HERO_ASSET`：独立、清晰、品牌化的商品 hero shot / end-card asset。

每项 `product_presentation` 必须绑定 `role`、`mode`、source asset identity、beat / Shot、entry / exit intent、transform intent、occlusion / tracking / lighting needs、graphic / sound cue，以及 capability classification。需要真实手持、contact、tracking、mask、depth、occlusion、perspective、cast shadow、lighting 或 camera matching 时，必须保持 `REQUIRES_SOURCE_GENERATION_STRATEGY` 或 `REQUIRES_RUNTIME_CAPABILITY`；普通 2D overlay 不得把它升级为 supported。

`graphic_treatment.role` 至少区分 `DIALOGUE_SUBTITLE`、`HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA` 与 `BRAND_END_CARD`。除 `DIALOGUE_SUBTITLE` 外，不得投影到 `CaptionTrack`。每项 commercial graphic 必须保留 placement、safe area、subject/product avoidance、entrance、exit、keyword emphasis、brand token 与 product/audio synchronization intent。

`sound_cue.role` 至少区分 `DIALOGUE`、`VOICE_OVER`、`MUSIC`、`SFX`、`REVEAL_HIT` 与 `INTENTIONAL_SILENCE`。它表达 advertising event 与同步关系，不拥有 samples、mix result 或 loudness truth；这些仍投影到 P4 audio authoring request，并由同一 `ResolvedTimeline` 与 render invocation完成。

### Projection And Capability Boundary

`AdCreativePlan` compiler 必须产生 typed Shot proposals 与 composition requirements，并在当前 `CompositionSpec` / HyperFrames expression surface不足时 fail closed。后续 Runtime slice可以最小扩展现有 `CompositionSpec` 和受审计的 HyperFrames source generator，以表达 constrained 2D product graphics与 commercial typography；不得开放任意 HTML、JavaScript、external CSS/font 或 event handler，也不得绕过 source audit。

当前能力判断固定为：

| Intent | Current classification |
| --- | --- |
| Dialogue / accessibility subtitle | `SUPPORTED_CURRENTLY` through `CaptionTrack` |
| Fixed 2D transform / opacity / z-order | `SUPPORTED_CURRENTLY` only where current composition layer accepts the asset type |
| Commercial text hierarchy / kinetic typography | `REQUIRES_RUNTIME_CAPABILITY` |
| Image-on-generated-video graphic reveal | `REQUIRES_RUNTIME_CAPABILITY` until the canonical layer/type gate and adapter support it |
| Provider-native in-scene product | `REQUIRES_SOURCE_GENERATION_STRATEGY` plus evidence / review |
| Tracked or masked physical product interaction | `REQUIRES_RUNTIME_CAPABILITY` or a separately approved source strategy |

HyperFrames 本身足以承载受限 2D graphics，不代表 AI-VIDEO adapter 已经表达这些能力。历史或 repo 外 FFmpeg 成片中的静音、固定黑底字幕、hard-cut product card 与 finalization bypass 也不得归因为 HyperFrames；只有 canonical `CompositionSpec -> ResolvedTimeline -> HyperFrames` execution与receipts才能证明正式链路行为。

### Explicit Non-Goals

本 follow-up 不建设第二 timeline、第二 renderer、第二 durable writer、新 Asset Registry、通用大型 Motion Engine、复杂 3D/AR tracking 系统、十几个广告 service/Agent，也不把 `CaptionTrack` 扩张成万能广告排版层。Composition Playbook 保持 Development Governance advisory surface，不成为 Runtime owner；任何 repo 外 finalization script 也不得成为 Production escape hatch。

### Acceptance Boundary

只有在 versioned `AdCreativePlan` schema、validator/compiler、typed projection、focused tests、canonical HyperFrames adapter evidence与 exact-snapshot Harness receipt全部存在后，才能声明该 bridge implemented。即使实现完成，真实手持/遮挡/光照匹配仍需独立 source或compositing evidence；technical render PASS 仍不等于 P6、human Final Acceptance或广告效果。

## Workflow State Machine

```text
INPUT
  -> G0 PRODUCT_TRUTH_READY
  -> G1 AUDIENCE_ANGLE_APPROVED
  -> G2 HOOK_AD_BEATS_COHERENT
  -> G3 PRODUCT_PRESENTATION_FEASIBLE
  -> G4 COPY_AUDIO_SYNCHRONIZED
  -> G5 STORYBOARD_SHOTS_TRACEABLE
  -> G6 RUNTIME_HANDOFF_VALID
  -> G7 AD_LOGIC_QC_PASS
  -> PACKAGE_READY
  -> optional VARIANT_DERIVATION
```

### Gate Semantics

- **G0**：商品 identity、assets、rights、facts、allowed/prohibited claims complete；任何医疗 / 治疗效果表达都不可进入下一阶段。
- **G1**：audience、pain point、angle、promise、proof 与 objective一致。
- **G2**：Hook 在第一秒可观察；每个 ad beat有 role、message、duration 与因果；不是固定五秒素材拼盘。
- **G3**：商品在 intro、demo/payoff、hero/CTA中有明确 mode；unsupported physical integration 阻止 handoff。
- **G4**：广告图文 role完整；商品名至少一次可见或可听；audio coverage无非 intentional gap；copy/product/audio cues可追溯。
- **G5**：每个 beat映射至少一个 Shot，每个 Shot反向追溯一个 beat；产品、talent 与 set state明确。
- **G6**：handoff不伪造 Provider、timeline、renderer或 acceptance；Runtime gaps分级清楚。
- **G7**：truth、product presentation、copy hierarchy、audio、CTA、brand closure无 blocking finding。

## Ad QC Contract

V1 pre-handoff Ad QC 至少检查：

1. 所有 claim 可追溯到 Product Truth source；
2. 商品正式名称至少一次可见或可听；
3. Hook、benefit、proof、CTA 不互相矛盾；
4. 商品首次出现、demo/payoff、hero shot 与 CTA 的 beat完整；
5. 商品 presentation mode不把 graphic overlay伪装成物理 interaction；
6. presenter hand/action 和 source framing为 product placement预留可执行空间；
7. `DIALOGUE_SUBTITLE` 与 advertising graphics roles分离；
8. headline、benefit、product label、CTA、end card 有信息层级和 cue binding；
9. 每个 beat的 audio intent有覆盖，非 intentional gap 为 blocker；
10. 每条 on-camera spoken line 绑定 exact speaker、Shot、verbatim script 与 lip-sync requirement；
11. native/generated source audio有明确 keep/mute/replace/trim policy，Shot opening noise risk进入 P6 requirement；
12. Shot duration由 ad beat需要驱动，不是机械等长 cut；
13. hero shot、brand closure 与 CTA均存在；
14. Runtime capability gap被显式标记，不由 prose 或 fallback隐藏。

Ad QC 是 authoring preflight，不评价实际画面、lip-sync、compositing、audio stream、watchability、P6 或广告效果。

## External Method Adoption

### `tengbot/aiads-skills`

- 可参考 Hook taxonomy、direct-response sequence、product-benefit-proof 与 variant dimensions；
- 不安装、不 fork、不 vendor；当前未发现明确 license；
- 不采用 UGC testimonial 作为默认路线；
- 不复制其六个平级 Skill，避免 trigger collision。

### `HiAPIAI/awesome-ai-video-workflows`

- 可独立重写 / attribution-safe 吸收 Product Truth、claim ledger、Shot start/end state、product contact/shadow QC 与 one-variable variant discipline；
- 不整体安装，不作为 dependency；
- 不采用其 Provider execution、installer、parallel storyboard/runtime 或 HiAPI handoff；
- 若未来复制 MIT 文字或模板 bytes，必须保留对应 license notice 与 source attribution。

### `Hainrixz/claude-ads`

- 只借鉴薄 orchestrator、progressive disclosure、typed artifacts 与 fail-closed aggregation；
- 不采用 19 Skills + 7 agents 的 account/campaign architecture；
- 不采用 live ad APIs、publishing、budget、performance optimization、persistent user profile 或 media runtime。

## Skill Package Architecture

推荐一个主 Skill 加按需 references：

```text
.agents/skills/ecommerce-ad-workflow/
├── SKILL.md
├── references/
│   ├── product-truth-and-claims.md
│   ├── audience-angle-and-proof.md
│   ├── hooks.md
│   ├── ad-beat-sequences.md
│   ├── product-presentation.md
│   ├── advertising-copy-graphics.md
│   ├── audio-pacing-and-coverage.md
│   ├── creative-variants.md
│   ├── runtime-handoff.md
│   ├── ad-qc.md
│   └── external-method-sources.md
├── schemas/
│   ├── ecommerce-ad-input.schema.json
│   └── ecommerce-ad-production-package.schema.json
├── templates/
│   ├── 30s-vertical-product-ad.input.example.json
│   └── 30s-vertical-product-ad.package.example.json
└── scripts/
    └── validate_contract.py
```

不拆成 `ad-hook`、`ad-script`、`ad-product-truth`、`ad-variation` 等平级 discoverable Skills。阶段知识通过 progressive disclosure按需加载，避免 context/discovery 噪声和责任重叠。

## Compatibility And Failure Behavior

- 不修改 public CLI、Production schema、Manifest、Registry 或 artifact layout；
- 不新增 runtime dependency；validator 保持 local、deterministic、no-network、no-write；
- package 是 authoring artifact，不登记为 implemented Production surface；
- Runtime materialization、asset import、Provider execution 与 render必须显式进行；
- claim source、rights、product asset、CTA destination或 capability缺失时 fail closed；
- 不 fallback 到 `open-video`、外部 ad Skill、AI comic Skill 或 ad account system；
- schema drift必须 bump contract version并维护明确 compatibility；
- rollback只移除 Skill package、tests与 routing，不触碰任何 Production state。

## Acceptance Criteria

1. `.agents/skills/ecommerce-ad-workflow/SKILL.md` 可被 Codex discovery，且触发描述只覆盖电商商品广告。
2. Skill 明确拒绝 AI comic / episode / cliffhanger / serial input，不调用 `ai-comic-workflow`。
3. Valid 30 秒 `9:16` input产生 schema-valid `EcommerceAdProductionPackage`。
4. Product Truth、claim ledger、rights、allowed/prohibited claims 与 required disclaimer均可验证。
5. 商品正式名称至少一次可见或可听，否则 G4 fail closed。
6. 每个 ad beat、Shot、product presentation、copy role 与 audio cue互相可追溯。
7. `PHYSICAL_INTERACTION_REQUIRED` 在缺乏可执行 source/runtime capability时阻止 handoff；不得降级为假装手持的 PNG overlay。
8. `DIALOGUE_SUBTITLE` 与 `HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`CTA`、`BRAND_END_CARD` 分离。
9. audio coverage完整；非 intentional silent window阻止 `PACKAGE_READY`。
10. on-camera dialogue 的 speaker、verbatim line、Shot 与 lip-sync requirement完整。
11. source-audio lead-in / noise policy存在；Workflow只提出 trim/fade/P6 requirement，不冒充实际修复。
12. creative variants一次只改变一个 declared variable，并列出 held constants。
13. `runtime_handoff` 不含 Provider、credential、permit、Manifest、timeline、render、P6 或 activation fields。
14. Existing `ResolvedTimeline`、HyperFrames、`ProductionStateCommitter`、P4/P6 ownership不变。
15. 不安装或依赖三个外部 repos，不新增 `skills-lock.json` external dependency。
16. No network、no Provider、no media generation、no Production write 的 contract tests通过。
17. Package只请求 video delivery；不得把 source/product still当作最终交付物。
18. Harness 对 exact Skill/test/control-plane delta运行 mandatory checks并产生 fresh receipt。

## Verification Strategy

Implementation 时至少提供：

- schema / validator unit tests；
- valid 30 秒 vertical product-ad fixture；
- Product Truth / claim / rights failure fixtures；
- forbidden AI comic fields tests；
- product presentation feasibility tests；
- advertising copy role separation tests；
- audio coverage and intentional-silence tests；
- one-variable creative variant tests；
- runtime-handoff forbidden-field tests；
- Codex Skill discovery / progressive-disclosure tests；
- Harness routing与 exact staged snapshot verification。

任何 live Provider、ComfyUI、media、subjective typography、product compositing、audio stream、P6、Final Acceptance 或广告效果都不属于本 Skill V1 verification。

## Repository Evidence

- `src/ai_video/production/models.py`：current creative、Shot、audio、caption、composition 与 timeline contracts；
- `src/ai_video/planning/video_planner.py`：single-Shot readiness boundary；
- `src/ai_video/production/shot_router.py`：provider-neutral generation resolution；
- `src/ai_video/production/video_generation.py`：Provider execution service；
- `src/ai_video/production/composition.py`：canonical timeline resolution；
- `src/ai_video/production/hyperframes.py`：default renderer adapter；
- `src/ai_video/production/state_commit.py`：唯一 Production writer；
- `docs/v0.2-runtime-baseline.md`：当前 implemented / unsupported composition truth；
- `docs/superpowers/specs/2026-08-21-ai-video-video-planner-subagent.md`：per-Shot planner non-goals；
- `AGENTS.md`：external Skill advisory-only 与 Production ownership contracts。

## Final Boundary

`ecommerce-ad-workflow` 的唯一产品价值是把商品事实与广告决策变成结构化、可验证的 authoring package。它不做 AI 漫剧，不调用 AI 漫剧 Workflow，也不成为媒体生产、投放或 campaign management 系统。
