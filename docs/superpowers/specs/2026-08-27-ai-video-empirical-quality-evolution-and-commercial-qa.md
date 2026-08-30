---
surface_id: empirical_quality_evolution
canonical: false
spec_status: proposed
implementation_status: not_started
live_status: partial
quality_status: partial
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: empirical-quality-evolution/0.1
---

# AI-VIDEO Empirical Quality Evolution And Commercial QA Specification

## Status

Proposed。本 Spec 将 2026-08-27 session 中已经形成的产品方向、质量边界、实验顺序与
Commercial QA 分层收敛为一个可复核 contract。它不是 implementation plan，也不改变当前
Production Runtime truth。

本 Spec 不授权代码修改、Manifest/schema migration、Provider 或 paid call、媒体生成、自动
repair、candidate activation、P6 / Final Acceptance、训练、发布、commit 或 push。只有用户后续
明确接受本 Spec 并单独授权相应 slice 后，相关行为才可实现。

动态实现状态仍由 `docs/v0.2-runtime-baseline.md` 拥有。本文中的历史媒体结论只对所引用的 exact
artifact 有效，不自动升级为 Production qualification、active capability、P6、Final Acceptance 或
release truth。

## Product Decision

AI-VIDEO 当前优先目标不是 SaaS、批量生产、更多 Gate、更多 schema 或更强的 Console，而是成为用户
本人可以长期使用的视频生产系统。

当前开发策略固定为：

```text
真实视频
  -> uninterrupted 1.0x human verdict
  -> exact failure evidence
  -> bounded single-variable repair or provider experiment
  -> reusable failure taxonomy
  -> evaluator shadow benchmark
  -> only then promote stable rules into an existing Gate
```

不得反转为：

```text
继续扩 Gate / policy / schema
  -> 假设 coverage 完整
  -> 期待未校准 evaluator 自动逼出满意视频
```

## Verified Current State

Verification date：2026-08-27。

### Quality Architecture

当前已接受的 top-level architecture 保持不变：

```text
Gate 1: Universal Production QA
  -> Gate 2: Domain-Specific Acceptance
       -> exactly one selected Domain profile
  -> existing P6 Review / Repair lifecycle
  -> Final Acceptance rollup
```

- `UniversalQualityGateCoordinator` 已提供显式、non-persistent Gate 1 ordering。
- Ecommerce 已有 typed Gate 2、canonical Production caller 与 existing P6 / Final Acceptance closure。
- Drama 与 Ecommerce 已在 architecture 上分离；Drama 是独立 Gate 2 profile concern，不复用 Ecommerce
  rubric。
- 当前仓库仍没有 formal Drama authoring workflow、typed Drama acceptance profile 或 canonical Drama
  application caller。
- `ShotReadinessGate.READY` 仍只表示 pre-submit structural binding、eligibility 与 required assets，不表示
  post-media quality、P6、activation 或 Final Acceptance。
- `ProductionStateCommitter` 仍是 durable review、repair 与 Final Acceptance 的唯一 writer。

本 Spec 不创建第三个 `Commercial QA Gate`。Commercial requirements 只能进入 existing Ecommerce
Gate 2 profile/evidence seam；shared technical requirements继续由 Gate 1 或既有 Runtime owner负责。

### Drama Human PASS Boundary

`E0-G` exact development artifact 为 770 frames at 24 fps，约 32.083 秒。用户对该 exact output 明确给出
full-speed subjective `HUMAN PASS`，并接受人物步速明显偏快作为 non-blocking observation。

因此“第一条超过 30 秒、用户本人完整正常速度观看后接受的视频”在 Drama / continuity development lane
已经出现。下一阶段不再重复追逐同一个 first-pass milestone，而是验证该能力是否可复用。

该结论不表示 E0-G 是完整 Ecommerce ad、canonical Drama Production candidate、P6、Final Acceptance、
publication-ready output 或 universal Provider qualification。

### Ecommerce Human Boundary

Qingyan v4-v9 形成连续的 empirical pattern：targeted Agent/technical checks 多次报告 PASS 或
`issues: []`，用户随后仍因对白/推荐缺失、freeze/seam、人物和相机不连续、产品重复、静帧运动、
产品机制错误、before/after 不成立、后段无配音、表演和节奏问题给出 human `FAIL`。

这证明当前 Gate envelope 擅长 identity、coverage、freshness 和 structural correctness，但真实 evaluator
尚不能从 MP4 稳定推导全部 commercial findings。Gate 的存在不等于 evaluator 已实现。

当前 exact Qingyan v10 local preview 为：

```text
artifacts/qingyan-miao-ad-20260826-v10/final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4
SHA-256 44e153f748189acffc15951bcf842eea11d2a6a4f00efacd8af1e61ab824b455
```

该 artifact 已有 full decode、technical Agent Gate 与 project-local MCP evidence，状态仅为
`PASS_FOR_HUMAN_REVIEW`。用户 uninterrupted viewing/listening final verdict仍为 pending。它不是
Ecommerce `HUMAN PASS`、Production candidate、P6、Final Acceptance 或 published output。

## Problem Boundary

当前最大风险不是 Ecommerce 与 Drama 共用 Gate。该 architecture 问题已经解决。

当前主要风险是：

```text
Gate infrastructure and evidence lifecycle
  > real evaluator coverage
  > stable human failure taxonomy
  > repeatable generation and repair recipe
```

具体表现为：

- requirement ID 存在，但 injected evaluator 可能只返回形式完整的 findings；
- generic analyzer 的 `issues: []` 会对真实 human failure产生 false negative；
- human verdict散落在版本记录与对话中，尚未形成完整的 whole-video calibrated corpus；
- 同一个 Qingyan candidate经过多轮 targeted repair后仍不断暴露新 failure class；
- narrow technical、continuity或Shot PASS经常被误读成whole-video satisfaction；
- 一条成功视频仍不能证明跨题材、跨SKU或跨Provider复用。

因此，在 empirical understanding收敛前继续扩大 subjective Gate rules，会把未理解的质量判断过早冻结成
policy，并制造错误 PASS、错误 FAIL 或不可信 `coverage_complete`。

## Goals

- 将个人 uninterrupted 1.0x whole-video verdict保持为当前最终主观接受权威；
- 用 3-5 条不同视频验证 Drama与Ecommerce生产能力的复用，而不是继续累计同一视频的小版本；
- 把 exact artifact、human verdict、failure span、repair variable与outcome绑定成可比较 evidence；
- 只自动化稳定、可测、低歧义的 structural、truth与delivery requirements；
- 让不成熟 evaluator先以shadow mode运行，并用human labels测量false positive/false negative；
- 保持 Universal Gate、Domain Gate、P6、Q0与Final Acceptance的owner边界；
- 给 Commercial QA 六个关注项定义不同的进入时间、证据权威与promotion条件；
- 让 Seedance只回答明确Provider capability hypothesis，不成为随机fallback；
- 只有实际证据证明收益后，才投资 selective rebuild、batch production或evaluator fine-tuning。

## Non-Goals

- 不新建第三个top-level `Commercial QA Gate`；
- 不重新设计已分离的 Universal/Ecommerce/Drama architecture；
- 不扩张 `ShotReadinessGate` 为post-media quality owner；
- 不把Qingyan-specific规则写成Universal或all-SKU policy；
- 不把Hook Density、CTR、CVR、ROAS、retention等market或creative optimization指标当成Production
  correctness；
- 不把technical score、single metric、MCP tool success或`issues: []`当成人类满意度；
- 不在本阶段训练、微调、自动选择Provider、自动repair或自动激活；
- 不优先建设Production Console、API server、queue、SaaS或batch UI；
- 不允许aggregate score抵消required `FAIL`或`NOT_EVALUATED`；
- 不用development PASS外推Production、P6、Final Acceptance或release truth。

## Resource Allocation Contract

在下一轮 3-5 条不同视频验证完成前，planned development allocation为：

| Work | Allocation | Boundary |
| --- | ---: | --- |
| 真实generation、整片观看与selective repair | 55% | 以whole-video human verdict结束每个cycle |
| generation workflow、continuity与Provider单变量实验 | 20% | 包含bounded Seedance实验；一次只改变一个变量 |
| exact human failure evidence与taxonomy | 15% | 不扩张为第二Production truth owner |
| evaluator shadow benchmark | 10% | 不拥有Production veto或PASS authority |
| Gate expansion与Production Console | 0% planned | 只处理真实blocking correctness regression |

Gate或Console若出现会阻断真实实验的deterministic bug，可作为interrupt修复；不得因此形成新的长期
infrastructure stream。

## Human Acceptance Contract

### Whole-Video Verdict

每条候选视频至少必须绑定：

- exact artifact identity与SHA-256；
-观看设备/目标环境；
- `1.0x` playback speed；
- 是否uninterrupted完整观看与试听；
- exact verdict：`HUMAN_PASS`或`HUMAN_FAIL`；
- 最多三个blocking findings；
- 每个finding的time span、requirement/failure category与可观察描述；
- reviewer明确接受但不阻断的concerns；
- verdict时间与reviewer pseudonymous identity。

`HUMAN_PASS`的含义是用户愿意原样使用该exact artifact。只有“可以继续review”“technical PASS”或
“某个Shot可以”不得升级为whole-video `HUMAN_PASS`。

### Failure Repair Decision

对一个whole-video `HUMAN_FAIL`：

- failure局限于不超过两个Shot或一个deterministic composition/audio surface时，MAY执行一次
  selective repair；
- failure要求重写whole-ad causality、product mechanism或多数Shots时，必须停止同一版本链并将其归档为
  failure evidence；
- 同一个candidate不得无限演化为v11、v12等版本而不验证经验是否能迁移到新brief；
- 每次repair必须声明changed variable、held constants与预期关闭的exact failure；
- repair后的新artifact必须获得新的whole-video human verdict，旧FAIL不得被改写。

### Storage And Ownership

本 Spec只定义最小evidence content，不授权新的dataset writer或第二human lifecycle。

- Production review/repair/final acceptance仍归`ProductionStateCommitter`；
- Q0 / `QualityExperienceRecordV1`仍是advisory structured experience owner；
- `docs/record_for_agent/`仍是curated human-readable historical evidence；
- future Console只能是evidence authoring surface，不得直接写Manifest或签发Final Acceptance；
- 在单一structured capture owner被独立接受前，任何临时capture不得被称为canonical Production truth。

## Failure Taxonomy Contract

### Immediately Automatable

以下requirements具有稳定、可确定、低歧义measurement seam，应优先自动化或维持现有自动化：

- exact SHA/content identity、registered bytes、provenance与path containment；
- decode、container/codec、duration、fps、resolution、aspect、frame/sample count；
- audio track presence、declared dialogue window中的long silence、clipping与measured loudness；
- black/freeze、exact duplicate frames、declared motion window中的long hold；
- deterministic clone padding、unexpected reverse/minterpolate、known white flash或hard cut；
- missing Shot/asset、Shot order、timeline span、caption/safe-area structural violation；
- stale/missing/tampered evidence、partial requirement coverage与unknown outcome；
- per-Shot Gate失败后继续submit下一Shot；
- Provider OOM、no MP4、duration contract mismatch与duplicate submit/poll/fetch；
- deterministic authored copy/VO/CTA与sealed Product Truth/claim ledger的exact binding。

### Human-First And Evaluator-Shadow

以下requirements当前不得由未校准automatic evaluator独占PASS：

- Drama motivation、causality、relationship logic、performance、emotional progression与payoff；
- 1.0x下的identity、camera velocity、motion-tail、screen direction与seam可感知性；
- product fidelity、packaging/label perceptual integrity与product appearance balance；
- product physical mechanism、usage order、contact、occlusion与interaction plausibility；
- before/after是否可信成立；
- dialogue、voice、lip-sync、表演、音色、字幕与声音语义是否自然对应；
- edit rhythm、视觉层级、产品出现频率、审美、Hook effectiveness与CTA persuasiveness；
- 一个瑕疵是否足以阻止用户原样使用成片。

Evaluator可生成requirement-level evidence proposal，但required不确定性必须为`NOT_EVALUATED`，不得通过
总分或confidence threshold自动变成PASS。

## Commercial QA Entry Contract

Commercial QA不是一个新top-level Gate。每项requirement必须进入以下owner之一：

- deterministic Ecommerce authoring preflight；
- existing Gate 1 / Delivery technical policy；
- existing Ecommerce Gate 2 exact-target evidence；
- human acceptance；
- non-blocking evaluator shadow benchmark。

### Current Surface Mapping

当前Qingyan Ecommerce profile已经包含：

- `ad.hook.first_second`；
- `shot.product.packaging_identity`；
- `shot.product.label_fidelity`；
- `shot.product.interaction`；
- `ad.product.packaging_consistency`；
- `ad.audio.coverage` / `ad.audio.product_recommendation` / `ad.audio.voice_continuity`；
- `ad.cta.brand_closure`；
- `ad.copy.claim_compliance`。

这些IDs证明rubric envelope存在，不证明MP4 evaluator已实现或已校准。下一slice的主要工作若获授权，应是
增加可信measurement/evidence producer，而不是继续增加名称或新Gate lifecycle。

### Promotion Matrix

| Commercial QA | Current treatment | First eligible promotion point | Required evidence authority |
| --- | --- | --- | --- |
| Hook Density | shadow metric；不作为quality hard Gate | 至少3-5条不同广告后再复核；universal promotion禁止 | human creative verdict；future format-specific experiment |
| Product Fidelity | exact input lineage自动校验；output fidelity由human hard-block | 至少3个SKU、30-50个labeled Shot findings与held-out calibration后 | human或calibrated automatic；plain automatic不能PASS |
| Usage Correctness | SKU-specific human hard requirement | SKU usage truth与10-20个同类labeled clips收敛后 | source-grounded human；calibrated evaluator只可逐步替代 |
| Claim Grounding | authoring fail-closed已适用；final-media coverage应优先补齐 | v10 verdict后、下一条新Ecommerce candidate前 | deterministic authored asset/script binding；generated content human fallback |
| Audio Loudness | measurement已存在；threshold尚须selected Delivery profile | selected platform/listening profile明确后即可加入Gate 1 | EBU R128 measurement + policy；mix quality仍由human |
| CTA Presence | authoring与profile requirement已存在；actual-media presence应优先补齐 | v10 verdict后、下一条新Ecommerce candidate前 | deterministic timeline/graphic/audio binding + human readability |

### Hook Density

`ad.hook.first_second`与Hook Density必须分开：

- 第一秒存在至少一个sealed、observable Hook cue属于authoring/runtime presence correctness；
- 一秒内多少visual/audio/copy cues、是否过载、是否抓人属于creative optimization；
- Hook Density不能成为Universal threshold；
- future rule必须绑定exact ad format、platform context与human evidence；
- CTR、retention或hold-rate只能作为market outcome evidence，不能反推Production PASS。

### Product Fidelity

现在可自动阻断的只包括exact product reference、approved first-frame、source asset/provenance与declared
binding。Generated video中的瓶形、颜色、cap、Logo、label、scale、perspective、lighting、hand contact与
occlusion仍由human拥有PASS权威。

Automatic Product Fidelity只有在以下条件全部满足后才可成为blocking authority：

1. 至少覆盖3个不同SKU；
2. 至少30-50个requirement-level labeled Shot findings；
3. PASS、不同failure classes与hard negatives均存在；
4. 有独立held-out set；
5. 与human agreement至少90%；
6. held-out critical cases中没有false PASS；
7. missing/ambiguous observation仍返回`NOT_EVALUATED`。

### Usage Correctness

Usage correctness必须先由每个SKU的sealed truth定义：

- allowed action sequence；
- required part removal/retention；
- application location与direction；
- forbidden actions；
- supporting package、instruction、source或explicit user confirmation。

Qingyan的“先开大盖、喷头露出后才能喷”可作为Qingyan-specific requirement，不得推广成all-spray
universal rule。没有source-grounded usage truth时，Gate必须`NOT_EVALUATED`，不得由模型常识猜测。

### Claim Grounding

Authoring阶段的allowed/prohibited claim ledger继续fail closed。Final-media检查遵循：

- deterministic overlay、caption与approved VO script必须逐项匹配sealed claim ledger；
- exact detected unsupported claim为`FAIL`；
- generated dialogue、OCR或ASR无法可靠判定时为`NOT_EVALUATED`并进入human review；
- extraction没有发现claim不得自动解释为“没有违规claim”；
- disclaimer不得把未授权、medical、absolute或quantified claim转为allowed。

### Audio Loudness

Audio Loudness归Gate 1 / Delivery policy，不归Ecommerce semantic evaluator：

- measurement使用existing EBU R128 integrated LUFS与true peak evidence；
- threshold必须来自preselected Delivery/listening profile，不得从单个v10的`-13.9 LUFS`硬编码；
- missing measurement或missing profile为`NOT_EVALUATED`；
- out-of-range为`FAIL`；
- dialogue intelligibility、BGM是否压人声、音色与听感仍由human判断。

### CTA Presence

CTA presence hard requirement只证明：

- exact CTA graphic或audible CTA进入active timeline；
- CTA绑定final beat/Shot与approved destination；
- required display/playback span实际存在；
- CTA未被裁掉、漏渲染或完全遮挡。

CTA是否有说服力、措辞是否优秀、用户是否愿意点击仍是human/market concern，不得由presence PASS外推。

## Seedance Experiment Contract

### Eligible Use

Seedance只能用于回答一个predeclared Provider capability hypothesis。至少满足一项：

1. 同一个sealed Shot已在H3/T8完成两个受控attempt，并重复出现同一疑似model-capability-limited
   failure；
2. synthetic/illustrated lane需要exact terminal-frame I2V continuation，且实验目标是复核既有positive
   continuity evidence；
3. 一个新official capability/profile明确提供当前stack缺失的reference、motion carrier或input mode，且
   exact capability evidence、budget、egress与permit均已满足。

### Required Controls

- same creative intent、input identity、duration与acceptance requirements；
- 只改变Provider/model/profile一个变量；
- submit前固定human/evaluator rubric；
- 一次bounded submit，无blind retry、fallback或追加variants；
- paid/remote execution仍须existing Paid Provider Gate、task-scoped authorization与per-Shot post-media
  Gate；
- output必须与current H3/T8 baseline做requirement-level comparison；
- fetched或technical PASS不得自动成为activation、P6或quality acceptance。

### Ineligible Use

不得使用Seedance：

- 修复subtitle、timeline、audio mix、static overlay、duplicate packshot等deterministic问题；
- 在current candidate尚无human verdict时随机寻找“更好看”variant；
- 作为H3/T8失败后的automatic fallback；
- 假设first-frame-only I2V能自动解决真人identity、camera velocity或motion-tail continuity；
- 在formal capability不支持required multi-anchor/reference组合时放宽request contract。

Existing evidence显示synthetic exact-terminal continuation有positive signal，但T8 -> H3 -> Seedance mixed
live-action lane曾因identity与camera continuity被用户否决。因此Seedance不是默认continuity repair。

### Continue And Stop

实验继续条件：selected requirement相对baseline明确改善，且没有引入新的critical human failure。

实验停止条件：

- exact capability不支持required inputs；
- outcome unknown或evidence identity不完整；
- 同一failure class无requirement-level改善；
- 新增critical identity、camera、product或usage failure；
- 需要通过多变量变化才能解释结果。

## Validation Phases

### Phase 0: Close Current Ecommerce Human Decision

Hypothesis：v10已关闭v4-v9的主要blocking findings，并达到用户愿意原样使用的标准。

Required action：用户在目标设备、正常音量、`1.0x`下uninterrupted完整观看和试听exact v10，并给出
`HUMAN_PASS`或`HUMAN_FAIL`。

Continue：

- `HUMAN_PASS`：冻结exact artifact，不继续润色；进入Phase 1。
- `HUMAN_FAIL`且不超过两个localized blocking surfaces：只允许一次bounded selective repair，再取得新
  whole-video verdict。

Stop or shrink：

- failure需要重写whole-ad logic、多数Shots或product mechanism；
- 一次repair后仍产生新的unrelated failure class；
- verdict缺exact SHA或不是完整1.0x观看。

Stop时保留v4-v10作为failure corpus，不继续无限版本链，转向新brief验证知识迁移。

### Phase 1: Reproducibility Across Five New Videos

Hypothesis：当前成功不是单一seed、单一场景、单一SKU或单一repair chain的偶然结果。

Validation set：

- 3条不同内容的Drama 30s；
- 2条不同产品或不同creative structure的Ecommerce 30s；
- 同一片的小版本不得计作新的validation video。

Continue：

- 5条中至少3条whole-video `HUMAN_PASS`；
- 至少包含2条Drama PASS与1条Ecommerce PASS；
- 大多数PASS不超过一次localized repair；
- 每条都有exact artifact-bound human evidence。

Stop or shrink：

- 少于3条PASS；
- 每条PASS均依赖whole-video rebuild；
- 只有原E0-G相同setup可以PASS；
- Provider variance或uncontrolled confounder阻止归因。

Stop时停止evaluator/Gate expansion，优先收缩到generation workflow、continuity、authoring与Provider
predictability。

### Phase 2: Failure Corpus And Evaluator Shadow

Hypothesis：重复failure classes已经稳定到可以测量evaluator，而不是继续发明taxonomy。

Entry conditions：

- Phase 1已有至少3条不同视频的exact human labels；
- 至少存在两个跨视频重复的failure classes；
- 每个finding具有time span、observed symptom与human verdict；
- PASS examples与hard negatives均存在。

Continue：

- evaluator可以在不看human label时输出requirement-levelfinding；
- confusion matrix、critical false PASS与`NOT_EVALUATED` rate可计算；
- evaluator error能够回指具体failure category或missing evidence。

Stop or shrink：

- taxonomy仍由每个新视频大幅重写；
- evaluator只会复述prompt或返回总分；
- automatic findings与human verdict没有可解释对应；
- missing evidence被错误升级为PASS。

### Phase 3: Promote Stable Rules

Hypothesis：至少一个repeated requirement已经具备稳定measurement、owner和低误报 adjudication。

Promotion order：

1. deterministic truth、CTA、loudness与structural rules；
2. calibrated Product Fidelity或Usage Correctness；
3. format-specific creative metrics；
4. Hook Density只在独立evidence支持时考虑，永不成为Universal rule。

Continue：

- rule在held-out evidence上达到predeclared agreement目标；
- critical false PASS为0；
- false block rate可接受且能通过`NOT_EVALUATED`保守处理；
- owner、profile/version、exact target与failure evidence均content-addressed；
- promotion不增加Gate 3、第二P6 writer或automatic Final Acceptance。

Stop or shrink：

- threshold依赖单一视频或单一SKU；
- rule需要总分抵消required failure；
- human仍频繁推翻automatic PASS；
- implementation主要增加schema/lifecycle而不是measurement能力。

### Phase 4: Selective Rebuild, Batch And Training

Selective rebuild only begins after at least five real localized repair events。Hypothesis是只重建failure frontier
可节省成本与时间，同时不降低whole-video human pass rate。

Continue：

- 相对full rebuild节省至少30%的wall time或paid/local compute cost；
- repaired whole-video human pass rate不低于full rebuild baseline；
- continuity、timeline、audio与evidence invalidation保持correct；
- repair没有频繁传播到unaffected Shots。

Stop：收益低于30%、failure经常跨Shot传播，或selective repair导致更多continuity regression。

Batch production only begins after 3-5条不同视频稳定PASS、成本/耗时区间可预测，并且failure handling不依赖
临场手工救火。

Evaluator fine-tuning only begins after：

- 至少200个稳定、requirement-level labeled clips/segments；
- taxonomy与rubric version冻结；
- positive、negative、hard-negative与held-out splits完整；
- prompt/rule/VLM-based evaluator已达到可测平台期；
- fine-tuning target明确优于继续prompt/calibration；
- training output仍只作为evaluator，不能拥有Manifest、activation或Final Acceptance。

对个人生产系统，如果existing evaluator + human review已满足成本和质量目标，可以永久不fine-tune。

## Production Console Trigger

Production Console在以下任一条件前不进入主要开发资源：

- 至少20次完整whole-video review event证明manual capture成为真实时间瓶颈；
- evidence遗漏、wrong-artifact verdict或无法定位failure span在独立cycles中重复至少3次；
- 已有accepted single human evidence owner与ingestion contract，Console只作为authoring UI；
- UI能够绑定exact SHA、播放位置、verdict、failure tag与reviewer，而不写Manifest或自动推进P6。

没有这些证据时，Console是premature product surface。

## Ownership And Compatibility

| Concern | Owner | Frozen boundary |
| --- | --- | --- |
| Universal hard correctness | Existing Registry/media/timeline/render/audio/caption owners | Domain PASS不得绕过hard failure |
| Gate 1 ordering | `UniversalQualityGateCoordinator` | explicit、non-persistent、no Gate 2 guessing |
| Ecommerce Gate 2 | Existing Ecommerce acceptance profile/coordinator | exact-target evidence；no second lifecycle |
| Drama rubric | Future independently accepted Drama workflow/spec | 不复用Ecommerce rubric |
| Durable P6/repair/final acceptance | `ProductionStateCommitter` | sole writer；no Console/evaluator write |
| Timing/order/frame/sample | `ResolvedTimeline` | no Provider/domain alternate timeline |
| Advisory corpus | Q0 / Quality Intelligence | no Production mutation or verdict ownership |
| Whole-video subjective acceptance | Exact human verdict | 不由technical score或MCP success替代 |
| Market outcome | Future separate analytics/experiment owner | 不属于Production acceptance |

本 Spec不改变current schemas、hashes、Manifest、Registry、artifact layout、public CLI、renderer、timeline、
Provider selection、P6 APIs或Final Acceptance semantics。任何future implementation若需要这些变化，必须由
独立accepted spec/plan定义migration、rollback与executable verification。

## Acceptance Criteria

本 Spec只有在以下内容均被明确接受后，才可升级为`canonical: true` / `spec_status: accepted`：

1. 产品目标明确为个人长期生产系统，而非SaaS-first或Gate-first。
2. E0-G被准确记录为exact Drama/continuity development HUMAN PASS，而非Production或all-domain PASS。
3. v10保持`HUMAN_FINAL_ACCEPTANCE_PENDING`，直至用户对exact SHA给出完整verdict。
4. Quality architecture保持exactly two top-level post-media gates。
5. Ecommerce、Drama与AI Comic只作为Gate 2 profiles，不成为额外lifecycle owners。
6. `ShotReadinessGate`、P6、Q0、Final Acceptance与Market outcome边界保持不变。
7. 下一阶段主要资源投入real video/human feedback/failure taxonomy，而非Gate/Console expansion。
8. 每个阶段均明确hypothesis、continue条件与stop/shrink条件。
9. Commercial QA六项均有明确owner、进入时间、evidence authority与promotion条件。
10. Claim Grounding、CTA Presence与Audio Loudness不会与Product Fidelity、Usage Correctness、Hook Density
    使用同一automatic promotion规则。
11. Hook Density不成为Universal或immediate hard Gate。
12. Product Fidelity与Usage Correctness在calibration前保持human-first。
13. Seedance只用于bounded、one-variable、capability-specific实验，不成为fallback。
14. evaluator在promotion前保持shadow并报告requirement-level confusion evidence。
15. fine-tuning、selective rebuild、batch production与Console均有evidence-based start gate。
16. 本 Spec不授权Provider、媒体、Production mutation、implementation、commit、push或release。

## Verification Contract

本Spec本身的documentation verification必须至少执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m scripts.docs_contract_gate check
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness policy-audit
git diff --check -- docs/superpowers/specs/2026-08-27-ai-video-empirical-quality-evolution-and-commercial-qa.md
```

若本Spec后续被接受并注册为canonical surface，必须同步
`.agent/harness/docs-contracts.yaml`，并为exact accepted contract增加最小、non-duplicative assertions。

任何future code/executable tooling change仍必须按`.agent/harness/policy.yaml`对exact staged snapshot或exact
commit range生成fresh passing Harness receipt。本Spec的docs checks不能替代runtime tests、media evidence、
human verdict、P6或Final Acceptance。

## Evidence Anchors

- `docs/superpowers/specs/2026-08-25-ai-video-quality-gate-architecture-separation.md`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `src/ai_video/production/ecommerce_media_acceptance.py`
- `src/ai_video/production/ecommerce_quality_gate.py`
- `src/ai_video/production/commercial_visual_review.py`
- `.agents/skills/ecommerce-ad-workflow/scripts/contract_gates.py`
- `docs/record_for_agent/2026-08-24-shot-continuity-e0e-seed320005-replication.md`
- `docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md`
- `docs/record_for_agent/2026-08-22-t8-h3-seedance-mixed-shot-continuity-handoff.md`
- `docs/record_for_agent/2026-08-26-qingyan-t8-portrait-canvas-30s-composition.md`
- `docs/record_for_agent/2026-08-26-qingyan-v5-dialogue-seam-continuity-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v6-product-exposure-seam-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v7-final-two-shot-hard-cut-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v8-underarm-elder-dialogue-continuity-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v9-before-after-and-later-voice-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v10-cap-mechanics-and-moving-comparison-blocker.md`

## Out Of Scope

- implementation task decomposition或plan；
- new Runtime API、schema、Gate type、evaluator service或Console UI；
- new Drama authoring workflow或typed Drama Gate 2 implementation；
- Provider/model benchmark、live smoke、paid call或media generation；
- current v10 human verdict本身；
- training dataset construction、labeling job或model fine-tuning；
- selective rebuild implementation或batch production；
- Git commit、push、PR、release或publication。
