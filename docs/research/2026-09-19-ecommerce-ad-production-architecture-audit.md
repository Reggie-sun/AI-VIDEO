# AI-VIDEO Ecommerce Ad Production Architecture Audit

Date: 2026-09-19

Repository snapshot: current local checkout at `ae272598eecb49591c522aa690b7ad36a15b81b4`

Scope: source-level architecture audit; no Provider call, media generation, runtime mutation, or production qualification

## Executive Verdict

AI-VIDEO 已经不是“只有镜头生成”的项目。当前 v0.2 Production 层拥有一套相当扎实的底座：strict artifacts、exact-byte provenance、provider capability routing、durable generation phases、single-writer activation/recovery、canonical timeline、deterministic composition、shot barrier、whole-video review 与 Final Acceptance contracts。这些方面明显强于本轮大多数开源对比项目。

但它目前更准确的产品形态是 **Production SDK + Agent governance repository**，而不是一个可直接运行的“电商广告全自动生产系统”。真正缺失的是把已有能力串成一个 canonical application job：

```text
ProductInput
  -> verified ProductTruth
  -> AdBrief / CreativeConcept / Script
  -> Storyboard / ShotSpec
  -> ReferenceAsset
  -> bounded Generation + evidence-backed ShotQC / Repair
  -> canonical Assembly
  -> evidence-backed FinalQC
  -> platform Variants
  -> Export
```

当前最大的风险不是底层没有 contract，而是 contract 分布在 Skill、Production API、Agent instructions、tests 与 callback seam 中，缺少一个 runtime owner 把它们完整闭合。最严重的质量漏洞出现在当前 ecommerce domain gate 的最低 evidence contract：系统能证明 evaluator 看的是哪一份 exact bytes，却没有在该 finding schema 中强制可复核的 frame/time/OCR/ASR/object evidence；现有 focused E2E test 在未选择更强 final-output visual/human contracts 时，可用全 PASS lambda 完成 Final Acceptance。仓库已经存在更强的 `final_output_review`；它尚未被 ecommerce path 设为必选。Caption 是不同情况：timeline 含 captions 时，canonical CAPTION review 已由 `caption_aware_review_layer_runner` 强制执行，缺少 `CaptionReviewExecution` 会得到 `NOT_EVALUATED`。

本审计基于当前 dirty working tree，而不是 `origin/main` 或已发布版本。文中 `PRODUCTION` 表示当前 checkout 存在 canonical runtime 接线和 executable tests，不表示本轮完成了真实 Provider、真实商品、真实媒体或人工质量验收。

## Research Method

先对五个指定项目做 exact-commit source review，再检查 AI-VIDEO。外部项目检查了 README、目录结构、schemas、skills、workflow/runtime、state、tests、QC、retry 与 artifact handling，而不是只看项目介绍。Star 是 2026-09-19 的 GitHub API 快照，会随时间变化。

| Repository | Inspected commit | Stars snapshot | License observation |
| --- | --- | ---: | --- |
| [Generative-Media-Skills](https://github.com/SamurAIGPT/Generative-Media-Skills/tree/5519622e885abc60217a65c8e090bcb1d9830746) | `5519622` | 4,296 | MIT |
| [short-video-factory](https://github.com/YILS-LIN/short-video-factory/tree/7f66665a33bfe30ed76598846158cf512f93d01f) | `7f66665` | 5,452 | AGPL-3.0 |
| [Open-AI-UGC](https://github.com/Anil-matcha/Open-AI-UGC/tree/9fffcc1a9518ea9b07ce8947891141a8aa2bf418) | `9fffcc1` | 315 | MIT |
| [remotion-ad-video-skill](https://github.com/leosssvip-dot/remotion-ad-video-skill/tree/e734c0299474132366e8270e9cffaf9a26f2c5ed) | `e734c02` | 108 | MIT |
| [atlas-marketing-studio](https://github.com/AtlasCloudAI/atlas-marketing-studio/tree/18ec178052f6f97612813997613d88ce34b02fc5) | `18ec178` | 30 | README 声称 MIT，但未找到 `LICENSE`，GitHub API license 为 null |

额外搜索发现 `Creatify-AI/video-ad-generator`、`cutagent`、`dart` 等项目，但没有发现同时满足“更成熟的 source-level 端到端电商 production system”和“更高采用度”的新增项目；因此没有为了凑数量将 proprietary API wrapper 或低成熟度项目加入主矩阵。

## 1. Current Architecture

### 1.1 Public Legacy Workflow

当前 public CLI 只有 Legacy `0.1.x` 路径：

```text
Project YAML + Shot YAML
  -> src/ai_video/cli.py:_load_binding_and_template
  -> src/ai_video/cli.py:_cmd_run / _cmd_resume
  -> src/ai_video/pipeline.py:PipelineRunner.run / resume
  -> src/ai_video/workflow_renderer.py:render_workflow
  -> ComfyUI submit / poll / fetch
  -> FFmpeg normalize / stitch
  -> Legacy RunManifest.final_output
```

这条路径支持 `validate`、`run`、`resume`，但没有接入 v0.2 ProductTruth、AdCreativePlan、P6 review 或 Final Acceptance。这里的 `Run succeeded` 表示 Legacy stitch 成功，不表示满足电商广告 production contract。

### 1.2 v0.2 Production Python API

真实代码路径如下；虚线处表示由外部 Agent/application caller 组装，而不是当前仓库已有的单一应用入口：

```text
Input / Authoring
  .agents/skills/ecommerce-ad-workflow/scripts/contract_models.py
  EcommerceAdInput -> EcommerceAdProductionPackage
          . . . no runtime compiler / application entrypoint . . .

Planning / Contracts
  src/ai_video/production/models.py
  ProductionBrief -> Story -> Storyboard -> Shot
  src/ai_video/production/ad_creative.py:create_ad_creative_plan
  -> compile_ad_creative_handoff
  -> AdCreativePlan + CompositionSpec + CommercialExecutionProjection

Generation Routing
  src/ai_video/planning/video_planner.py:VideoPlanner.plan
          . . . caller supplies current plan/readiness context . . .
  -> ShotReadinessGate / prepare_shot_for_existing_production
          . . . caller injects context_loader and builds execution binding . . .
  -> src/ai_video/production/generation_feedback.py:GenerationFeedbackOrchestrator.prepare
  -> src/ai_video/production/shot_router.py:VideoGenerationResolver.resolve_requirement
  -> selected adapter compile/resolve
          . . . caller constructs the facade from the sealed binding/service . . .
  -> EcommerceVideoGenerationFacade

Sequential Generation / Shot Barrier
  src/ai_video/production/ecommerce_ad_coordinator.py:run_ecommerce_ad_generation
  -> VideoGenerationService.start
  -> submit / poll / fetch
  -> validate
  -> activate
  -> PASS permits next Shot; FAIL / NOT_EVALUATED stops

Assembly
          . . . injected activate_final_render callback . . .
  -> src/ai_video/production/composition.py:resolve_composition
  -> ResolvedTimeline
  -> src/ai_video/production/hyperframes.py:render_with_hyperframes
  -> ProductionStateCommitter activation

Whole-video Validation / Output
  src/ai_video/production/ecommerce_ad_coordinator.py:run_ecommerce_ad_production
  -> UniversalQualityGateCoordinator
  -> EcommerceQualityGateCoordinator
  -> P6 ReviewReceipt
  -> ProductionStateCommitter.record_final_acceptance
```

`run_ecommerce_ad_production()` 接受已经编译的 `handoff`、已经创建的 per-shot facades、render callback、hard-check callback、review callback 和 whole-ad evaluator。Codegraph 的 caller relationship 与 exact text search 都显示：仓库内 non-test application 没有调用它；直接 callers 是模块内部和 tests。因此它是一个真实、受测的 SDK seam，但还不是 packaged production application。

### 1.3 Canonical Runtime Owners

| Concern | Current real owner | Assessment |
| --- | --- | --- |
| Selected artifacts | `ProductionProject` / `load_production_project()` | strict、read-only、selected revision validation |
| Durable mutation | `ProductionStateCommitter` | single writer、atomic state、explicit recovery |
| Provider contract | `VideoProvider` + exact `VideoProviderRegistry` | injected exact lookup，未发现 silent provider fallback |
| Provider routing | `VideoGenerationResolver` | capability/requirement-first；resolver 不执行、不 fallback |
| Generation lifecycle | `VideoGenerationService` | durable start/submit/poll/fetch/validate/activate/resume |
| Dependency/invalidation | Dependency Graph | typed dependency 与 precise frontier |
| Timing/order | `ResolvedTimeline` | canonical frame/sample owner |
| Rendering | `HyperFramesAdapter` | canonical deterministic renderer path |
| QA lifecycle | QA policy/review receipts + committer | exact identity/currentness/final acceptance |
| Development verification | `scripts/agent_harness.py` + `.agent/harness/policy.yaml` | source-change Harness，不是广告 runtime orchestrator |

## 2. What AI-VIDEO Already Does Well

### PRODUCTION

以下能力有 canonical code path 与 executable tests 支撑：

| Capability | Evidence-backed assessment |
| --- | --- |
| Strict project artifacts | `ProductionBrief`、`Story`、`Storyboard`、`Shot`、Asset Registry 与 selected revisions 都是 machine-readable contracts。 |
| Ad plan compilation | `AdCreativePlan` 强制 hero、brand closure、CTA、product truth reference、claim reference、sound cue 与 Shot binding；`compile_ad_creative_handoff()` 生成 composition/projection handoff。 |
| Exact provider routing | Seedance、MiniMax H3/Hailuo、本地 Comfy T8、Vidu 等 adapter 接入共同 capability/request contracts；registry exact lookup 不 silent fallback。 |
| Durable generation | Submit intent、permits、phase state、fetch bytes、validation、activation 与 resume 都有 canonical state owner。 |
| Sequential Shot gate | 一个 provider Shot 未 PASS 时，后续 Shot 不 submit；activation 前重开 current evidence/checkpoint。 |
| Partial regeneration substrate | 每个 Shot/asset/attempt 有独立 identity；Dependency Graph 支持局部 invalidation，而非必然全 pipeline 重跑。 |
| Provenance | exact request、provider profile、selected inputs、artifact SHA-256、tool identity、review evidence 和 activation lineage 比对比项目更完整。 |
| Canonical assembly | `CompositionSpec -> ResolvedTimeline -> HyperFrames` 支持 visual spans、graphics、transitions、audio/caption binding 与 exact final media verification。 |
| Voice/caption primitives | Voice request/provider contracts、caption alignment/track、sample/frame mapping 与 renderer integration 已存在。 |
| BGM/SFX mixing | explicit audio tracks、trim、gain、fade、ducking 与 canonical mix path 已实现；不是简单把视频拼起来。 |
| Whole-video gate lifecycle | Universal gate、ecommerce gate、P6 review、Final Acceptance 有明确 state/currentness barrier。 |
| Crash/replay safety | unknown outcome fail closed、one-use permit、atomic commit、explicit recovery 与 exact replay semantics 扎实。 |

### PARTIAL

| Capability | Why only partial |
| --- | --- |
| Ecommerce authoring | Skill 有丰富 `EcommerceAdProductionPackage` JSON Schema 与 G0-G7 validation，但它被明确限定为 advisory authoring；Production runtime 没有 compiler/application bridge。 |
| Product Truth | Skill 能表达 facts、claims、sources；runtime `AdCreativePlan` 主要保存 source/claim IDs，未自动提取或验证商品事实。 |
| Automated ShotQC | gate 真正阻断，但 evaluator 内容可信度由 injected implementation 决定；finding 本身没有强制 observed evidence。 |
| Failure taxonomy | `generation_diagnosis` 很丰富；上层 ecommerce coordinator 把多种错误压成四类 stop reason，常见为 `SERVICE_STOP`。 |
| Retry/regenerate | attempt history、quota、decision、intervention 和局部重跑基础存在；没有 canonical unattended repair loop 把 decision 持续执行到 PASS/terminal budget。 |
| Voice-to-ad orchestration | TTS、routing、captions、mixing primitives 存在；从 ad script 自动生成、激活、排布到最终 QC 的应用层没有闭合。当前 checkout 还有未提交 voice-routing work，不能算 released truth。 |
| Music/SFX | import/mix contract 完整，但自动选曲、生成、license/rights、与广告语义同步的 job 没有闭合。 |
| Final-video QA | exact candidate/currentness 非常强；caption review 在适用时已经强制。当前 ecommerce path 尚未强制选择 stronger final-output visual/human contract，最低 domain finding 仍可能依赖 evaluator 自报 PASS。 |
| Resume | per-shot/provider/state recovery 强；不存在一个公开的全广告/campaign job 入口负责从商品输入恢复。 |

### EXPERIMENTAL

- `scripts/generation_feedback_driver.py` 是一次 prepare/execute/evaluate driver，不会自动执行下一个 repair decision，也不是通用 campaign runner。
- `artifacts/.../execute_t8_portrait_ad_batch.py` 这类 historical executor 自管 state/receipt，且明确是 development-only；不能当 canonical Production pipeline。
- hooks 中的 background video analysis queue 是 advisory capture，不是 synchronous gate 或 activation permit。

### DEAD / UNUSED

- 没有足够证据把某个 production module 判为 DEAD。`video_fake.py` 是 deterministic offline provider，有测试用途，不能因为不生成真实媒体就判死代码。
- `run_ecommerce_ad_production()` 可准确标记为 **unused by the packaged application / directly exercised mainly by tests**，但不能据此声称它从未被外部手工调用，也不应删除。

## 3. Missing Ecommerce Ad Pipeline

`DONE` 表示 runtime owner 与执行闭环存在；`PARTIAL` 表示 contract 或 primitives 存在但未形成完整 application path；`MISSING` 表示当前未找到 production executor。

| Lifecycle stage | Status | Current truth |
| --- | --- | --- |
| 商品 URL / 图片 / 信息输入 | PARTIAL | image/assets 可注册；未找到通用 product URL fetch/extract runtime。 |
| Product intelligence / ProductTruth | PARTIAL | Skill schema 和 claim validator 强；事实仍主要由 Agent/用户输入，缺 source capture、fact extraction 与 conflict adjudication service。 |
| Audience / persona / ad objective | PARTIAL | authoring schema 有字段和 gates；没有 runtime strategy owner。 |
| Ad brief | PARTIAL | `ProductionBrief` 与 ecommerce input 两层并存，缺 canonical compiler。 |
| Hook / Creative Concept | PARTIAL | Skill 与 `AdCreativePlan` 可表达；内容由 Agent author，缺统一 proposal/selection state。 |
| Script | PARTIAL | Story、beats、dialogue、narration contracts 存在；没有 ProductTruth-to-script application job。 |
| Storyboard contract | DONE contracts / PARTIAL application | strict `Storyboard`/`Shot` artifacts；生成和 approval 仍由外部 Agent 组合。 |
| Shot contract | DONE | intent、duration、assets、visual strategy、continuity、review policy 等 machine-readable。 |
| Reference Asset / identity | DONE contracts / PARTIAL empirical | exact asset/reference/fidelity contracts 强；真实一致性仍需模型/媒体证据。 |
| Provider routing | DONE | requirement/capability-first、exact provider selection、no silent fallback。 |
| Generate | DONE SDK | remote/local service phases、activation 与 resume 完整。 |
| Shot-level QC | PARTIAL | blocking gate 已接；evaluator evidence contract 仍不足。 |
| Failure classification | DONE substrate / PARTIAL propagation | diagnosis 有 typed categories；application stop result 丢失细节。 |
| Retry / regenerate | PARTIAL | 支持新 attempt 和局部失效；没有自动 bounded repair runner。 |
| Editing | DONE runtime / PARTIAL application | timeline 和 renderer 真实存在；ecommerce coordinator 用 injected render callback。 |
| Voice / TTS | DONE primitives / PARTIAL workflow | provider/asset/timeline path存在；未从广告脚本自动闭合。 |
| Subtitle | DONE primitives / PARTIAL workflow | caption alignment/render path存在；没有全广告 application owner。 |
| BGM / SFX | PARTIAL | timeline/mix存在；selection/generation/rights/semantic QC 不完整。 |
| CTA / end card | DONE contract | plan 强制 CTA 与 brand closure binding；最终视觉真实性仍依赖 QC。 |
| Final assembly | DONE runtime / PARTIAL application | HyperFrames 是 canonical owner；外层 job 不负责构造完整 assembly。 |
| Final-video QA | PARTIAL | lifecycle 强，也存在更强 observational contracts；当前 ecommerce application 没有强制选择它们。 |
| Platform-specific variants | MISSING executor | Skill 有 variant matrix；无 durable platform variant generator/validator/exporter。 |
| Batch generation | MISSING campaign runtime | sequential shots 不是 campaign queue；无多广告共享资产/预算/lineage owner。 |
| 最终 9:16 电商广告成片 | PARTIAL | 可以由专家/Agent 组合已有 SDK 做出，但还不是单一可恢复、可审计、无人值守的 product workflow。 |

## 4. Open-source Comparison

以下不是简单打分；每格描述 repository 内实际接线。`External` 表示核心能力委托给仓库外服务。

### 4.1 Authoring, Generation, and Media Contracts

| Project | Product input / truth | Creative / script | Storyboard / Shot contract | Provider abstraction | Image / video generation |
| --- | --- | --- | --- | --- | --- |
| AI-VIDEO | Skill schema 丰富；runtime bridge 缺失 | machine contracts 强，内容由 Agent author | strict artifacts + compiled handoff | exact capability/request/adapters，无 silent fallback | 多 adapter、durable lifecycle、exact bytes |
| Generative-Media-Skills | product assets/recipes；无 ProductTruth owner | campaign/UGC Skill recipes | keyframe guidance；无 durable storyboard/shot state | `schema_data.json` 较好，但 I2V 仍有 hard-coded switch；workflow external | shell/CLI submit-poll，返回 remote URL |
| short-video-factory | free-form prompt；无商品事实 | generic LLM text | 无；visuals 随机挑本地片段 | OpenAI-compatible text + EdgeTTS | 不生成 image/video，只消费素材 |
| Open-AI-UGC | prompt + images；无 ProductTruth | 用户 prompt | 无 | 四个 hard-coded MuAPI endpoints | 单次 provider clip |
| remotion-ad-video-skill | URL classification + asset harvest；claim blocker较好 | ad brief + concepts | storyboard artifact；部分 machine validation | renderer/tool choice，不是生成 Provider abstraction | deterministic Remotion/HyperFrames render |
| Atlas Marketing Studio | product image/text/assets；URL field未接 extraction | Drama/Skit 有 plan；主 Marketing UGC 一次 prompt | Drama 有 segment plan，主 UGC 近似单 Shot | shared Atlas client，但模型/workflow hard-coded | image + video paths 可运行 |

### 4.2 Post-production, Quality, and Operations

| Project | Voice / subtitle / music | Editing / assembly | QC / retry | Lineage / resume | Batch / variants | Agent / Harness |
| --- | --- | --- | --- | --- | --- | --- |
| AI-VIDEO | contracts 与 canonical mix 强；自动广告接线 partial | ResolvedTimeline + HyperFrames | blocking gates 强；semantic evidence与自动 repair partial | exact hashes、Manifest、recovery 强 | authoring only；executor missing | Skills advisory；development Harness 强但不是 runtime |
| Generative-Media-Skills | music/voice primitives；字幕链弱 | effects/lipsync primitives | manual approval，未发现 automatic gate/retry | request ID/manual；无 durable job manifest | parallel recipes/crops，不是 campaign runtime | agent-readable Skills；无 repository Harness |
| short-video-factory | EdgeTTS + SRT + Pixi captions + BGM | FFmpeg normalize/concat/loudnorm/mix | TTS retry；无 semantic/final QC | settings persistence，不是 job resume | UI 递归 batch；无 variant semantics | 无 agent/harness |
| Open-AI-UGC | provider native audio only | 无 | 无 QC/retry；submit-before-DB 有 orphan risk | DB URL/status + poll/webhook，exact bytes lineage弱 | 无 | 无 Harness/tests |
| remotion-ad-video-skill | render props 可带 captions/audio | staged still/preview/draft/final | checklist/manual QA；final 可绕过 recorded QA | file artifacts，manifest无 content hash | concepts/variants guidance | Skill + package/concept validators |
| Atlas Marketing Studio | native audio/TTS；无字幕/BGM | browser FFmpeg concat、reference edit/lipsync | polling retry较好；无 shot/final semantic QC | `getUrl` resume、atomic completion/refund；URL lineage | 无 campaign variants | polling/resume tests，非 Agent Harness |

### 4.3 Designs Worth Absorbing

#### Generative-Media-Skills

值得吸收：

- `core/media` 与 `library/*` 的分层，让低层 media tools 与高层 campaign/UGC recipes 解耦。
- [`schema_data.json`](https://github.com/SamurAIGPT/Generative-Media-Skills/blob/5519622e885abc60217a65c8e090bcb1d9830746/schema_data.json) 的 provider input catalog 思路，可用于减少 adapter capability metadata 重复。
- [`product-campaign`](https://github.com/SamurAIGPT/Generative-Media-Skills/blob/5519622e885abc60217a65c8e090bcb1d9830746/library/social/product-campaign/SKILL.md) 与 [`ugc-ads-workflow`](https://github.com/SamurAIGPT/Generative-Media-Skills/blob/5519622e885abc60217a65c8e090bcb1d9830746/library/social/ugc-ads-workflow/SKILL.md) 的小型、可组合、Agent-readable recipe 结构。

不应照搬：它本质上是 capability/recipe catalog；[`muapi-workflow`](https://github.com/SamurAIGPT/Generative-Media-Skills/blob/5519622e885abc60217a65c8e090bcb1d9830746/library/workflow/SKILL.md) 把 DAG/state 委托给外部服务，repository 内没有 durable ad job、QC、provenance、resume 或 assembly truth。AI-VIDEO 当前的 single writer、exact evidence 与 fail-closed lifecycle 更成熟。

#### remotion-ad-video-skill

最值得吸收的是 outer lifecycle：

```text
AdBrief -> Assets -> Concepts -> Storyboard -> Still -> Draft -> QA -> Final
```

具体参考：[`ad-brief-contract.md`](https://github.com/leosssvip-dot/remotion-ad-video-skill/blob/e734c0299474132366e8270e9cffaf9a26f2c5ed/skills/remotion-ad-video/references/ad-brief-contract.md)、[`validate-creative.mjs`](https://github.com/leosssvip-dot/remotion-ad-video-skill/blob/e734c0299474132366e8270e9cffaf9a26f2c5ed/scripts/validate-creative.mjs)、[`schema.ts`](https://github.com/leosssvip-dot/remotion-ad-video-skill/blob/e734c0299474132366e8270e9cffaf9a26f2c5ed/skills/remotion-ad-video/assets/remotion-template/src/schema.ts)、[`fast-ad-lab.mjs`](https://github.com/leosssvip-dot/remotion-ad-video-skill/blob/e734c0299474132366e8270e9cffaf9a26f2c5ed/scripts/fast-ad-lab.mjs)。

结论：**应该成为 AI-VIDEO 的外层 production contract，但不能原样照搬。** 每个 stage transition 必须落入现有 Manifest/Dependency/Review owners，并由当前 hash-sealed/content-addressed receipt 阻断；不能新建第二套 lifecycle，也不需要为此暗示新增 cryptographic signature subsystem。该项目自身的 storyboard 是 Markdown、asset manifest 无 hash、QA 多为 checklist，且 `final` 可直接运行，所以它的 staged UX 好于 AI-VIDEO，enforcement 弱于 AI-VIDEO。

#### short-video-factory

值得吸收的是生成之后的 deterministic post stack：

- narration duration 驱动 timeline；
- TTS 同步产生 SRT；
- subtitle rasterization 与 FFmpeg 分离；
- voice/BGM loudness、mixing 与 cancellable render；
- batch UX 的连续产出体验。

实际核心在 [`edgeTtsSynthesizeToFile`](https://github.com/YILS-LIN/short-video-factory/blob/7f66665a33bfe30ed76598846158cf512f93d01f/electron/tts/index.ts)、[`getVideoSegments`](https://github.com/YILS-LIN/short-video-factory/blob/7f66665a33bfe30ed76598846158cf512f93d01f/src/views/Home/components/VideoManage.vue) 和 [`renderVideo`](https://github.com/YILS-LIN/short-video-factory/blob/7f66665a33bfe30ed76598846158cf512f93d01f/electron/ffmpeg/index.ts)。

AI-VIDEO 不应复制其随机素材选择、无 storyboard、无 manifest/resume/QC 的做法；应把它的操作体验映射到已有 `ResolvedTimeline` 与 HyperFrames contract。

#### Atlas Marketing Studio

这是指定项目中最接近 runnable ecommerce application 的项目。值得吸收：per-shot reference generation、保存 `getUrl` 后的 polling resume、transient/terminal failure 区分、atomic completion claim、idempotent refund/compensation，以及应用层中间状态恢复。参见其 [workflow](https://github.com/AtlasCloudAI/atlas-marketing-studio/blob/18ec178052f6f97612813997613d88ce34b02fc5/src/lib/marketing-studio/workflow.ts) 与 [resume tests](https://github.com/AtlasCloudAI/atlas-marketing-studio/blob/18ec178052f6f97612813997613d88ce34b02fc5/test/marketing-resume.test.ts)。

不应吸收：主 Marketing UGC 绕过 plan、multi-shot 被分散在 Drama flow、plan failure 后自动改用 generic fallback、hard-coded model workflow，以及 URL-based lineage。该 fallback 会返回 `fallback: true` 与 detail，并非 silent；问题是它没有 fail closed。AI-VIDEO 的 exact state/provenance 更强，应该只吸收 application orchestration 和 operator UX。

#### Open-AI-UGC

可借鉴的只是 authenticated creation history、async webhook + poll fallback、capability-driven UI 与 reference upload UX。其 [`/api/generate`](https://github.com/Anil-matcha/Open-AI-UGC/blob/9fffcc1a9518ea9b07ce8947891141a8aa2bf418/src/app/api/generate/route.js) 在 durable Creation 写入前 submit，可能留下付费 orphan；webhook authenticity、empty outputs、BYOK polling 也有明显缺口，不适合作为 production control-plane 参考。

## 5. Architecture Gaps

以下只列九个核心问题。

### P0 — Blocks a Reliable Production Pipeline

1. **缺少 canonical end-to-end application job。** Public CLI 是 Legacy；v0.2 ecommerce path 是由 caller 注入大量对象/callback 的 SDK。没有一个 durable job 从 `ProductInput` 编译到 `FinalAcceptance/Export`，也没有 job-level resume/status/result contract。

2. **ProductTruth / AdBrief authoring 未接入 runtime。** Skill 有最丰富的商品事实、claim、audience、hook、audio、CTA、variant schema，但 runtime 不 import 它；`AdCreativePlan` 接收 source/claim IDs，不负责抓取、提取、冲突判定或建立可追踪事实快照。

3. **当前 ecommerce minimum policy 没有强制接入 strongest final-output visual/human contract。** `EcommerceRequirementFinding` 只有 `requirement_id`、`verdict`、`rationale`；adjudicator 检查 profile、ordered coverage 和 all PASS，却不要求 frame/time span、OCR/ASR、object/identity observations 或 raw analyzer artifact hash。`final_output_review.py` 已能要求完整 observations、visual finding validity 与 human 1x evidence；问题是 ecommerce production 并未把该 contract 设为 mandatory。Caption-quality 不属于这个缺口：timeline 含 captions 时已强制 canonical CAPTION review。现有 E2E test 在未选择 final-output contract 时，用全 PASS lambdas 和 `_passing_payload()` 即可完成 Final Acceptance。这证明的是 application/policy wiring gap，不是所有 P6/final-output contract 都能被 lambda 绕过。

4. **Assembly 不是 ecommerce coordinator 的完整 owned stage。** `run_ecommerce_ad_production()` 依赖 injected `activate_final_render`。因此 script/voice/caption/BGM/SFX/CTA 到 `CompositionSpec` 的构造、draft/final render 和 stage receipts 仍由外部 caller 负责。

5. **Failure 后没有 canonical automatic bounded repair loop。** Gate 能正确停止；generation decision/diagnosis 能提出下一步；但没有 application runner 自动执行 evidence repair、request repair、regenerate、re-review，直到 PASS、budget exhausted 或 unknown outcome。当前 stop reason 还会把 typed errors 压成 `SERVICE_STOP`。

### P1 — Seriously Limits Quality or Automation

6. **广告 audio/caption/post primitives 没有形成一个广告级编排器。** TTS、captions、BGM/SFX 和 mixing 都存在，但没有从 sealed script/audio intent 生成资产、排 timeline、验证 audibility/lip-sync/caption/CTA，再进入 final gate 的单一 workflow。

7. **没有 durable campaign / platform variant owner。** Skill 的 variant matrix 只是 authoring；没有共享 ProductTruth/asset lineage、单变量 variant delta、局部 invalidation、platform profile、逐 variant FinalQC、batch budget 和 export bundle。

8. **控制面分裂会让 Agent/subagent 形成临时 glue。** Skills 被正确限制为 advisory，Development Harness 也明确不调度 Agent或媒体；但缺少 runtime application owner 后，Agent 必须手工连接 authoring、facades、render callbacks 和 evaluators。instructions 不能替代 executable orchestration，也不能证明 subagent 遵守了同一 production gate。

### P2 — Capability Enhancements

9. **Still/Draft/Final 未成为同一 render owner 下的正式阶段。** 当前 renderer 可以 source-audit、lint、check、render 和 verify，但 assembly-level still/draft/final 缺 machine-readable stage intent 与 blocking receipt，导致布局、商品尺度、字幕安全区等问题可能过晚暴露。

## 6. Proposed Target Architecture

目标是演进现有架构，不推倒重写。保持以下不变：`ProductionStateCommitter` 仍是唯一 writer；Dependency Graph 仍独占 invalidation；`ResolvedTimeline` 仍是唯一 timing owner；HyperFrames 仍是默认 renderer；Provider adapter 不拥有 activation；QA/P6 不由 Skill 决定。

建议增加一个薄的 `EcommerceProductionJob` application owner，负责阶段推进，但所有 durable mutation 仍委托现有 committer。推荐状态：

```text
INGESTED
 -> PRODUCT_TRUTH_READY
 -> BRIEF_READY
 -> CONCEPT_SELECTED
 -> STORYBOARD_SEALED
 -> REFERENCES_ACCEPTED
 -> SHOTS_ACCEPTED
 -> ASSEMBLY_DRAFT_ACCEPTED
 -> FINAL_ACCEPTED
 -> VARIANTS_ACCEPTED
 -> EXPORTED
```

| Layer | Input -> Output / schema | Owner + validator | Failure / retry boundary / artifact |
| --- | --- | --- | --- |
| ProductInput | URL/images/text -> `ProductInputSnapshot` | new thin ingestion service; URL/asset policy validator | `INPUT_UNAVAILABLE`, `RIGHTS_UNKNOWN`, `SOURCE_DRIFT`; retry fetch only; exact source snapshot + hashes |
| ProductTruth | input snapshot -> `ProductTruthSnapshot` + `ClaimLedger` | evolve ecommerce authoring models into runtime-neutral contracts; source/conflict validator | `FACT_UNSUPPORTED`, `SOURCE_CONFLICT`; retry extraction/adjudication only; facts/claims with source spans |
| AdBrief | truth + operator goal -> `AdBrief` | compiler into existing `ProductionBrief`; claim/audience/offer validator | `BRIEF_INCOMPLETE`, `CLAIM_UNSAFE`; return to brief; sealed brief artifact |
| CreativeConcept | brief -> bounded concepts + selected concept | existing/new ad creative compiler | `CONCEPT_UNSUPPORTED`, `TRUTH_DRIFT`; regenerate/select concept only; proposal + selection receipt |
| Script | concept + claims -> `Story` + copy/audio intent | existing Story owner + ecommerce compiler | `SCRIPT_CLAIM_VIOLATION`, `DURATION_UNFIT`; rewrite affected beats; sealed script |
| Storyboard | script -> `Storyboard` | existing artifact owner; beat/coverage validator | `BEAT_UNCOVERED`, `PACING_INVALID`; regenerate affected beats; storyboard artifact |
| ShotSpec | storyboard -> existing `Shot` + `AdCreativePlan` + commercial projections | existing compiler/router contracts | `SHOT_UNROUTABLE`, `CTA_UNBOUND`, `AUDIO_UNCOVERED`; revise affected Shot; exact Shot/projection artifacts |
| ReferenceAsset | truth/Shot -> registered references + approvals | Asset Registry + existing commercial source owners | `IDENTITY_UNPROVEN`, `PRODUCT_FIDELITY_FAIL`; regenerate/reapprove one reference; content-addressed asset/evidence |
| AssetGeneration | missing images/audio -> activated assets | existing provider services + committer | `CAPABILITY_UNSUPPORTED`, `PROVIDER_*`, `OUTCOME_UNKNOWN`; per asset attempt; intent/receipt/fetched bytes |
| VideoGeneration | accepted Shot/reference -> candidate MP4 | existing `VideoGenerationService` | typed provider/runtime failure; per Shot attempt; exact request/submission/fetch candidate |
| ShotQC | exact MP4 + Shot rubric -> `ShotAcceptanceReceipt` | existing `GeneratedCommercialShotEvidence` + project-local video-analysis bridge + `VideoGenerationService.validate` | `TECHNICAL`, `SEMANTIC`, `CONTINUITY`, `PRODUCT_FIDELITY`, `EVIDENCE_GAP`; repair one Shot only; observed evidence + receipt |
| Assembly | accepted assets + `CompositionSpec` -> still/draft/final render | `resolve_composition` + HyperFrames + committer | `TIMELINE`, `AUDIO_CAPTION`, `LAYOUT`, `RENDER`; rebuild affected DAG frontier; render artifacts + stage receipts |
| FinalQC | final bytes + ad goal -> Final Acceptance | Universal + ecommerce + final-output owners | `FINAL_GOAL`, `NO_REGRESSION`, `PLATFORM`; fix owning layer, not score override; evidence bundle + acceptance receipt |
| VariantGenerator | accepted master + variant deltas -> variant jobs | new campaign application owner over existing artifacts/DAG | `VARIANT_CONFLICT`, `PLATFORM_PROFILE_FAIL`; regenerate only delta/dependents; variant spec + lineage |
| Export | accepted master/variants -> delivery bundle | new thin delivery packager that reuses Registry/committer and owns no second activation state | `EXPORT_MISMATCH`, `PACKAGE_INCOMPLETE`; repackage only; MP4s + manifest + provenance/QC summary |

`Brief -> Assets -> Storyboard -> Still -> Draft -> QA -> Final` 应采用为 operator-facing outer contract；内部仍映射到上述现有 owners。Still、Draft、Final 只是同一 render lifecycle 的不同 proof purpose/quality profile，不能创建新的 renderer、timeline 或 second Manifest。

统一 failure family 应复用既有 `AiVideoError`、generation diagnosis 与 QA verdict，而不是发明并行 vocabulary：

```text
INPUT_TRUTH / RIGHTS / CONTRACT / CAPABILITY
PROVIDER_RETRYABLE / PROVIDER_TERMINAL / OUTCOME_UNKNOWN
MEDIA_TECHNICAL / SHOT_SEMANTIC / CONTINUITY / PRODUCT_FIDELITY
AUDIO_CAPTION / COMPOSITION / FINAL_GOAL / PLATFORM
```

每个 failure 必须带 `owner_stage`、`affected_artifact_ids`、`evidence_refs`、`retryability`、`invalidation_frontier`。`OUTCOME_UNKNOWN` 永远不能 blind retry。

## 7. Harness Design

### 7.1 Keep Two Planes Explicit

不要把现有 `.agent/harness/policy.yaml` 扩成媒体生产引擎。

1. **Development Harness**：继续负责 changed-path routing、exact staged/commit snapshot、tests、architecture checks 和 receipt。它证明代码/contract change 被正确验证，不证明某条广告成片合格。
2. **Production Harness**：新增薄的 `EcommerceProductionJobRunner`，只编排现有 canonical owners。它消费 sealed job input、检查 stage receipts、调用现有 service/committer，并返回可恢复的 `next_action`。它不让 Agent、Skill、Provider、renderer 或 analyzer直接写 Manifest。

### 7.2 Required Production Gates

| Gate | Required input | PASS condition | Blocking behavior |
| --- | --- | --- | --- |
| G0 Product Source | exact URL/image/text snapshot | source readable、rights/policy known、hash fixed | STOP before truth extraction |
| G1 ProductTruth / Claims | facts + claim ledger + source spans | every active claim supported、conflicts adjudicated | STOP before creative generation |
| G2 Brief / Storyboard / Shot | brief, concept, script, storyboard, ShotSpec | coverage、CTA、audio、duration、capability requirements complete | STOP before asset/provider work |
| G3 Reference | registered exact assets | identity/product fidelity/rights PASS | STOP before dependent Shot submit |
| G4 Per-Shot Media | exact MP4 + exact intent/rubric + prior accepted state | all required technical/semantic/continuity findings PASS | no next-Shot submit; route bounded repair |
| G5 Assembly Draft | still/draft + canonical timeline | layout、safe area、captions、audio、CTA coverage PASS | no final render/activation |
| G6 Whole Video | exact final MP4 + final-output contract | universal + ecommerce + no-regression findings PASS | no P6/Final Acceptance/export |
| G7 Variant / Platform | exact variant + platform profile | encoding、duration、safe zone、copy/CTA and semantic parity PASS | block only affected variant/export |

### 7.3 Close the “Model Says PASS” Loophole

一个 finding 不得只保存 verdict/rationale。建议 machine-readable minimum：

```json
{
  "requirement_id": "...",
  "verdict": "pass|fail|not_evaluated",
  "observation_refs": ["artifact-id#observation-id"],
  "time_ranges_ms": [[0, 1200]],
  "frame_refs": ["frame-artifact-sha256"],
  "measurement_refs": ["ocr/asr/object-track/probe artifact"],
  "evaluator_identity": "tool@version",
  "rubric_hash": "...",
  "reason": "..."
}
```

规则：

- exact bytes、rubric、tool identity 与 observation artifacts 必须同时 seal；
- 没有 evidence 的 required finding 必须是 `NOT_EVALUATED`，不能靠完整字段结构升级为 PASS；
- OCR/ASR/object/fidelity/continuity 等不同 requirement 不能被单一总分覆盖；
- human-required requirement 没有人类 evidence 就不能被 VLM PASS 替代；
- final gate 必须读取 shot receipts 和 final render observations，不能只重用 provider success 或 draft evidence；
- evaluator 的 controlled presentation、raw response、parser version 与 adjudicator version 都要可追踪。

### 7.4 Retry and Regeneration Controller

Production Harness 只根据 typed failure 采取 bounded action：

```text
evidence missing -> EVIDENCE_REPAIR_FIRST
request/rubric mismatch -> rebuild exact request, no media retry yet
known quality failure -> one-variable repair -> new attempt identity -> full G4
provider retryable failure -> bounded retry with new one-use permit
outcome unknown -> STOP, explicit recovery only
final composition failure -> invalidate owning audio/caption/layout node and dependents
```

每个 job 固定 task-level submit ceiling、per-stage attempt ceiling、elapsed/resource budget。Retry 不得切 Provider、改变 claim、降低 rubric 或 silent fallback；Provider switch 是新的 routed candidate，必须重新证明 capability 与 quality evidence。

### 7.5 Agent and Subagent Contract

- Agent/Skill/subagent 只可以产出 proposal、authoring artifacts 或调用 Production Harness；不能自行建立 `.state.json`、直接激活 candidate、跳过 gate 或将 tool success 当 acceptance。
- Harness receipt 必须记录 exact job/artifact hashes，而不是记录“哪个 Agent 说已完成”。
- parent Agent 保持 final claim responsibility；subagent output 在被 canonical loader/validator 接受前没有 production authority。
- Development Harness 继续验证 code diff；Production Harness 负责媒体 job。两者 receipt 可互相引用，但不能互相替代。

## Recommended Sequence

1. 先实现 `EcommerceAdProductionPackage -> ProductionBrief/Story/Storyboard/Shot/AdCreativePlan` 的 canonical compiler 与 job schema；这是连接已有资产的最短路径。
2. 复用现有 `final_output_review` 与 project-local video-analysis controlled presentation，把 per-finding observed evidence 变成 ecommerce G4/G6 的 mandatory runtime contract；保留当前适用时已强制的 caption-quality path，删除电商最低 policy 上 bare PASS compatibility。
3. 将 existing generation diagnosis/decision/service 串成 bounded repair driver，保留 unknown-outcome/permit/quota semantics。
4. 让 ecommerce application owner 构造 canonical `CompositionSpec`，接通 voice/captions/BGM/SFX/CTA，并引入 Still/Draft/Final stage receipts。
5. 最后增加 campaign/variant owner；它复用 ProductTruth、assets、Dependency Graph、ResolvedTimeline、HyperFrames 与 QA，不复制底层 pipeline。

## Verification Boundary

本审计验证的是当前代码结构与 focused executable behavior。没有调用 live Provider、没有生成或观看新媒体、没有进行人工广告质量验收、没有证明任何模型的真实商品一致性，也没有把外部项目 README 声明当作实际能力。外部项目结论绑定上述 exact commits；AI-VIDEO 结论绑定当前 dirty local checkout，后续合并/提交可能改变结果。

Fresh verification on the audited checkout:

- `77 passed in 63.83s`：`test_production_ecommerce_ad_coordinator.py`、`test_production_ecommerce_post_media_e2e.py`、`test_production_ecommerce_quality_gate.py`、`test_production_quality_gate_coordinator.py`、`test_production_ad_creative.py`。
- `237 passed in 11.52s`：`test_ecommerce_ad_workflow_skill.py`、`test_production_composition.py`、`test_production_captions.py`、`test_generation_feedback.py`。
- Codegraph 验证 `run_ecommerce_ad_production()` 的内部/test callers 与 `run_ecommerce_ad_generation()` 的调用关系；`rg` 复核 packaged non-test application caller 不存在。
- Harness inspection 将本报告映射为 `documentation`，要求 `scope_diff_check`、`docs_contract_check`、`policy_audit_check`、`product_runtime_skill_boundary_tests`；正式 receipt 在 exact staged snapshot 后生成。
