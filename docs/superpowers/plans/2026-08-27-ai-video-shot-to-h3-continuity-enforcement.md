# AI-VIDEO Dual-Domain Shot-to-H3 Continuity Enforcement Implementation Plan

**Goal:** 建立一套由 Drama 与 Ecommerce 共同复用、但不合并两类 domain rubric 的 Shot-to-H3 physical /
perceptual continuity core：approved Shot sequence 的跨 Shot 因果状态经唯一 sealed `GenerationIntent`、
pairwise causal transition contract 与 deterministic H3 compiler 后，减少怪运镜、compound motion、intent
drift 以及人物/道具/产品状态跳变；分别取得 Drama 与 Ecommerce exact HUMAN evidence 后，才把“dual-domain
proven”能力扩大到全 adapter、qualification、composition enforcement 与 Harness 收口。

**Scope:** Provider-neutral Shot semantic intent、camera/subject relation、pre-generation pairwise causal
readiness、一个 evidence-backed Local H3 pilot adapter 的 exact prompt compilation、符合当前 H3 frame 下限的
Shared Continuity Core、互相独立的 `M6-D Drama` 与 `M6-C Commercial` empirical lanes、每条 lane 各自的
exact whole-video HUMAN verdict，以及只有两条 lane 的 shared requirements 都有 exact evidence 后才执行的
remaining adapter、qualification、post-media pairwise evidence、composition 与 Harness 收口。Qingyan 只作为
Commercial regression oracle；不得代表 Drama acceptance 或整个 plan 的产品目标。

**Contract Surfaces:** `GenerationIntent`、`ProviderNeutralVideoRequirement`、`VideoPlanner`、
`ShotReadinessGate`、`ProviderRequestCompilationResult`、H3/T8 adapter compiler identity、
`ContinuityTransitionPolicy`、generic generated-Shot review evidence、`CompositionSpec` / `ResolvedTimeline`、
P6 / human evidence boundary、Harness changed-path routing。

**Invariants:** `ProductionStateCommitter` 仍是唯一 Production writer；`ResolvedTimeline` 仍是唯一 timing/
order owner；Router 仍独占 Provider/profile selection；adapter不得重创作 Shot、fallback 或降低 requirement；
Skill 只提供 advisory knowledge；Provider/media、activation、P6、Final Acceptance 与 publication 均不由本
Plan 自动授权。

**Current / Target Behavior:** 当前 generic H3/T8 adapter 把 provider-neutral `key=value; ...` prompt 原样
提交，P0/M0 又维护独立手写 three-field prompt；`GenerationIntent` 缺少 performance、visual treatment、
lighting、ambience、dialogue 与 music 的 typed upstream owner，camera contract 可缺 endpoint、可包含 compound
motion。v12 进一步证明 Shot 顺序正确不等于 `previous.close_state -> next.open_state` 因果可达：人物可无
bridge 出现/消失，产品可无交接改变 holder/hand/state，推荐可直接跳到使用。目标链改为：
`approved sequence + explicit causal edges + compatible conditioning -> sealed per-Shot GenerationIntent ->
pairwise readiness -> exact H3 three-field prompt -> bounded real-media experiment -> shared continuity verdict +
exactly one selected domain verdict`。四臂实验已把 forced scale transition / terminal snap 的主要原因收敛到
incompatible last anchor；随后 one-Shot causal handoff 又证明 compatible anchors 与明确动作链可完成可见
holder transfer。原 M6 Qingyan micro-sequence 最终得到 HUMAN watchability / commercial-baseline / assembly
acceptance `FAIL`，只构成 Commercial lane counterevidence；Drama lane已有accepted spec、fixture、baseline、
authoring package与execution-gate/exact-evidence-path，但仍没有HUMAN media verdict。目标状态必须
分别关闭两条 lane，不得用广告状态链证明剧情叙事，也不得用剧情 continuity PASS
证明产品呈现、claim、Hook、CTA 或 brand closure。

**Compatibility:** Historical `provider-neutral-video-requirement/1`–`/3`、existing compiled request、resolved
request、activation scope、compiler/profile hash 和 qualification profile 必须 bit-for-bit reopen/replay；新的
camera contract 采用 additive versioned branch，只用于 new attempts。旧 compiler/profile 不得被静默重解释，
也不得通过自动 migration 改写 existing Manifest、receipt 或 artifact identity。

**Out of Scope:** 新 camera Skill、Provider selection/fallback、未经单独授权的 live/paid submit 或媒体生成、
自动 repair、renderer/timeline replacement、新 P6 writer、跨 Drama/Ecommerce aggregate quality score、训练或
微调、将 development HUMAN PASS 升级为 Production/P6/Final Acceptance、在本 plan 内发明或实现
`ai-short-drama-workflow` / Drama schema / Drama runtime Gate、扩张现有 Ecommerce Gate 2、全面重写任何 external
Skill，以及清理历史 artifact-specific scripts。Drama authoring/rubric 必须先由独立 accepted workflow/spec
拥有；本 plan 只消费其 sealed requirement-level outputs。

**Acceptance Criteria:**

- H3/T8 pilot new attempt 缺少完整 open/close、action、performance、visual treatment、lighting、audio/music
  boundary、axis、camera path、camera-subject relation 或 camera endpoint 时在 Provider effect 前 typed BLOCKED；
- continuity-sensitive adjacent Shots 缺少可验证的 character presence、prop holder/hand/state、action phase、
  gaze/dialogue/motion bridge，或未由 selected domain owner 声明合法 ellipsis/reset/domain-specific cut 时，在
  compiler/Provider 前 typed BLOCKED；
- FL2VA first/last anchors 缺少同尺度/同构图可达性、duration-bounded endpoint compatibility 或 approved
  compatibility evidence 时，在 upload/Provider effect 前 typed BLOCKED；不得在失败后自动换 anchor、lane 或
  recipe；
- 一个 AI-VIDEO Shot 只能编译一个 `[Shot 1]` 和一个 `primary_camera_motion`；允许一个不构成第二 creative
  motion 的 stable `camera_subject_relation`，禁止 internal cut time 和 `[Shot 2]`；
- exact submitted H3 prompt 由 sealed requirement 确定性生成，并包含唯一且有序的
  `integrated_multimodal_description`、`overall_soundscape`、`non_diegetic_music`；
- pilot H3/T8 adapter 不再调用 generic neutral prompt 作为 new-attempt native grammar；其他 adapters 在首轮
  empirical gate 前保持不变；
- Shared Core 不编码 `Hook`、CTA、product proof、motivation、conflict、emotional payoff 或 cliffhanger；这些
  分别属于 Ecommerce 与 Drama domain owner，且任一 domain verdict 不得替代另一条 lane；
- `M6-D Drama` 只在独立 accepted Drama workflow/spec、sealed fixture/rubric 与 exact quality baseline 存在后
  执行；它必须取得剧情表演、blocking/eyeline、dialogue turn、叙事因果/情绪推进和 shared continuity 的
  requirement-level HUMAN evidence；
- `M6-C Commercial` 使用 accepted Ecommerce package、Product Truth/claim lineage 与 exact source-quality
  baseline，独立验证产品 presentation/demo/proof、Hook/pacing、CTA/brand closure 与 shared continuity；当前
  Qingyan `15.5s` assembly 是该 lane 的 HUMAN `FAIL`，不得重标为 PASS；
- 两条 lane 的 applicable shared requirements 与各自 domain requirements 都取得 exact HUMAN PASS 前，不得
  宣称 dual-domain proven，也不得继续执行 Milestones 7–9；
- post processing 不得创造或伪造 continuity PASS。`xfade`、dissolve、retime、interpolation、padding 可在
  typed montage、dream/time jump、scene reset、selected-domain cut 或已通过边界上的明确艺术/节奏用途合法
  存在，但不能替代缺失的 causal state change，且变换后的新 SHA 必须重新验收；
- 每条 lane 的 whole-video HUMAN PASS 分别绑定 exact final SHA、完整 `1.0x` full-speed/full-audio 播放、每个
  pairwise boundary、shared physical/perceptual findings 与该 domain 的独立 rubric；任何重编码或修复后必须
  重新验收新 SHA。Drama PASS 与 Commercial PASS 互不继承。

**Verification:** Phase A 使用 strict RED-GREEN focused tests、historical hash/reopen fixtures 与 pilot adapter
offline tests；Phase B-D / B-C 只在各自 accepted domain inputs 与适用 execution gates 下独立执行 bounded
micro-sequence、exact whole-video `1.0x` human playback 与 baseline comparison；Phase C 只有在两条 lane 都通过
后才运行 remaining adapter、composition/P6 regression、Architecture Gate、policy-routed Harness exact staged
snapshot receipt 与一次 `reviewer_xhigh` independent review。Offline acceptance 不执行 Provider、ComfyUI 或
媒体生成。

**Related Evidence:**

- `docs/record_for_agent/2026-08-26-qingyan-t8-portrait-canvas-30s-composition.md`
- `docs/record_for_agent/2026-08-26-qingyan-v5-dialogue-seam-continuity-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v6-product-exposure-seam-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v8-underarm-elder-dialogue-continuity-repair.md`
- `docs/record_for_agent/2026-08-22-t8-h3-seedance-mixed-shot-continuity-handoff.md`
- `docs/record_for_agent/2026-08-27-shot-continuity-m0-terminal-tail-v5.md`
- `docs/record_for_agent/2026-08-27-h3-conditioning-attribution-gate-stop.md`
- `docs/record_for_agent/2026-08-27-qingyan-v12-causal-recut-and-single-close.md`
- `docs/record_for_agent/2026-08-27-qingyan-v13-causal-handoff-experiment.md`
- `docs/record_for_agent/2026-08-28-h3-m6-causal-micro-sequence-gate-stop.md`
- `docs/superpowers/plans/2026-08-25-ai-video-quality-gate-architecture-separation.md`
- `docs/agent-primary-contract-matrix.md` (`Quality Gate Architecture Boundary`)
- `artifacts/qingyan-miao-ad-20260827-v12/authoring/authoring-contract.md`
- `artifacts/qingyan-miao-ad-20260827-v12/ecommerce-package.json`
- `artifacts/qingyan-miao-ad-20260827-v12/review/final-gate.md`

## Dual-Domain Revision And Current Status — 2026-08-28

原 plan 把 Qingyan regression evidence 误写成了唯一 empirical product target。当前修订保留 M1–M5 已实现的
provider-neutral Shared Continuity Core，并将 Phase B 拆成独立 domain lanes：

| Lane | Current status | What the status means |
| --- | --- | --- |
| `M6-D Drama` | `NOT_EVALUATED` / `STOP_BEFORE_SUBMIT` | B-D0 prerequisite complete后已获独立M6-D启动授权；canonical Shot 01 execution-intent overlay与three-line H3 prompt保持accepted/sealed。当前已显式选择local H3 quality candidate且runtime identity exact match，但canonical Router因sealed fixed `5.0s` requirement无法由profile的`124`-frame output contract表达而`blocked_capability`；没有生成exact request preview、persist/submit request或media/Production-state effect。详见`docs/record_for_agent/2026-08-29-drama-m6-d-shot-01-request-readiness-gate-stop.md` |
| `M6-C Commercial` | `HUMAN_FAIL` | Exact Qingyan `15.5s` assembly SHA-256 `c36bbb7b5bcdcd9312fcd74d521751502b22800a637ba788e4db1c7b97ef1c07` 在 watchability、commercial-quality baseline 与 assembly acceptance 上 FAIL；历史 per-Shot technical PASS 只保留在其证据层 |
| Dual-domain Phase B | `FAIL` | 两条 lane 未同时通过；M7–M9 继续 deferred |

Qingyan v12/v13、四臂 conditioning 与 causal micro-sequence 继续作为 Commercial / shared physical continuity
regression evidence；它们不是 Drama authoring、narrative continuity、performance 或 whole-scene acceptance
evidence。下方出现的 Qingyan、product、Hook、CTA 或 `commercial_cut` 只适用于 Commercial oracle/profile；
M1–M5 的 provider-neutral contracts 不因此变成 Ecommerce-owned。

v12 的新增 HUMAN evidence 作为 plan 的 blocking regression oracle：`4.500s` 人物/产品 holder 无桥接跳变，
`7.250s` 推荐直接跳到使用且老人消失，均为 pairwise causal FAIL；`13.250s` 因果顺序成立但表演自然度仍需
human；`17.042s` 语义可理解但人物重现和 camera seam 有缺陷；`24.333s` 可作为明确 commercial cut，但整体
pacing 仍由 human 判定。现有 `PASS_FOR_HUMAN_REVIEW` 与 `narrative-order-pass` 不能覆盖这些 findings。

**Completed Empirical Reconnaissance (not Milestone 6 PASS):** 四臂 A/B 只改 last anchor 后由 forced
transition/terminal snap/tail collapse FAIL 变为 technical PASS；I2VA first-only 与 upstream-current compatible
FL2VA 也 technical PASS。因此 incompatible last anchor 是 supported primary cause，FL2VA 普遍 lane mismatch、
Stock20 recipe/pin bundle 与 H3 model limitation 均不受该 evidence 支持。随后 exact Stock20 FL2VA causal
handoff Shot 取得 technical Shot Gate PASS，但其 prompt 为手写 sealed prompt、input Registry lineage 不是
Production-complete，不能验证 `GenerationIntent -> compiler`。将该 Shot 嵌回 exact 30s 后，holder transfer
PASS，但 character 在 `4.500s` 出现、`9.667s` 消失、`19.458s` 重现仍 FAIL；该 artifact 不满足 Milestone 6
Commercial lane 或 revised dual-domain HUMAN gate，也不授权继续 M7–M9，更不能作为 Drama evidence。

## Problem Boundary And Ownership

| Concern | Single owner in target design | Required boundary |
| --- | --- | --- |
| Director coverage、Shot purpose、bridge beat 与 Shot order | Approved AI-VIDEO Storyboard / Shot artifacts | `open-video` 只提供 coverage/advisory，不生成 runtime prompt或拥有 Production truth |
| Semantic continuity、character/prop/action causal state | Approved Shot artifacts projected into `GenerationIntent` and `ContinuityTransitionPolicy` | `hell-grind-aigc-skill` 只提供 advisory rules；repo-local typed validation独占执行 |
| Camera/shot language、camera-subject relation、action/gaze/sound bridge、pacing | Approved Shot artifacts projected into the same `GenerationIntent` / transition contract | `video-shotcraft` 是 authoring advisory，不限于 post motion，也不得形成第二 prompt owner |
| H3 wording、three-field grammar、single-take compression | `src/ai_video/production/_h3_prompt.py` | `h3-video` 只提供 H3 grammar guidance；compiler 只机械翻译 sealed facts，不补写 creative facts |
| H3/T8 workflow binding | Selected adapter | 只绑定 compiler output；不得接受 run-local prompt rewrite |
| FL2VA conditioning compatibility | Selected Shot requirement + adapter preflight | approved first/last anchors 必须同尺度、同构图且在 duration/action/camera path 内可达；不兼容时 authoring 显式改 anchor 或选择 I2VA，adapter 不自动 repair/reselect |
| Pre-generation pairwise reachability | `ContinuityTransitionPolicy` | 明确 carry、visible change、authorized ellipsis/release；不能用 Shot 顺序代替因果路径 |
| Post-media pairwise findings | generic generated-Shot review evidence in `review.py` | 同时绑定 source terminal window 与 target opening window；qualification-only source review 不扩张为通用 owner |
| Order、frames、trim、transition execution | `ResolvedTimeline` / P3 composition | transition执行不拥有或创造 causal/continuity verdict |
| Universal media validity and physical/perceptual continuity | existing Runtime validators、generic continuity evidence、P6 lifecycle + exact human evidence | analyzer/technical PASS 不得冒充 domain HUMAN PASS 或 Final Acceptance；shared schema 不拥有 domain rubric |
| Drama authoring、narrative continuity and acceptance | accepted `docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md` | 本 plan 不创建或改写该 owner；motivation、relationship causality、conflict、dialogue semantics、emotional progression、payoff/cliffhanger 不得由 physical continuity receipt替代 |
| Ecommerce authoring and commercial acceptance | `.agents/skills/ecommerce-ad-workflow/` + existing Ecommerce Gate 2 seam + exact human evidence | Product Truth/claims、Hook、product presentation/demo/proof、CTA、brand closure 只适用于 Commercial lane；不得冒充 Drama acceptance |
| Dialogue Performance / Lip-sync | per-Shot media review + selected domain human evidence | shared edge 只拥有 speaker turn、gaze/response 与 sound bridge obligation；对白语义、角色动机和情绪作用由 Drama rubric拥有 |
| Whole-program readability / pacing | exact whole-video human evidence + selected domain rubric | Drama scene readability 与 Ecommerce Hook/conversion pacing 分开；technical presence/timing 或 aggregate score不能代判 |

需要退休或替换的 old paths：

1. H3/T8 new attempt 通过 `video_compiler._compile_neutral_prompt()` 获得 native prompt；
2. new P0/M0 qualification 同时手写 semantic boundary 与 three-field prompt；
3. Agent 在 adapter 前手工重写 exact H3 prompt，且 receipt 只保存 hash、不保存可重建 translation lineage；
4. Shot advice 经 `video-shotcraft` / continuity prose / adapter prose 多次翻译后才进入 H3 prompt；
5. authoring package 用 `narrative-order-pass` 代替 `previous.close_state -> next.open_state` causal reachability；
6. continuity-claiming final composition 接受未绑定 pairwise boundary evidence 的 artifact-specific
   `tpad/xfade/flash/minterpolate/setpts` 修复；
7. FL2VA new attempt 只校验 bytes/roles，不要求 first/last anchor 的 scale、composition、motion/action endpoint
   在声明 duration 内可达，导致模型被迫吸附不兼容终点。

保持不变的 contracts：Provider Router、Paid Provider Gate、durable intent/one-use permit、unknown-outcome
recovery、Manifest/Registry writer ownership、P5 candidate、P6 verdict、P8 publication、Legacy CLI、
HyperFrames default renderer 与现有 historical replay。

Focused implementation command：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_h3_prompt.py \
  tests/test_production_video_intent_validation.py \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_comfy_t8_native_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_video_transition.py -q
```

## Major Milestones

M1–M5 是已经由 commit `d0abf74` 实现并通过 exact-range Harness 的 Shared Continuity Core。以下历史 milestone
细节继续作为 implementation lineage；dual-domain revision 不重写其已发生状态，也不把 Commercial fixture
specific fields 升级为 universal domain truth。Phase B 从修订后的 Milestone 6 重新开始。

### Milestone 1: Freeze Regression Oracles Before Contract Changes

**Files:**

- Create: `tests/test_production_h3_prompt.py`
- Create: `tests/test_production_video_intent_validation.py`
- Modify: `tests/test_production_video_requirement.py`
- Modify: `tests/test_planning_video_planner.py`
- Modify: `tests/test_shot_readiness_gate.py`
- Modify: `tests/test_production_provider_neutral_adapters.py`
- Modify: `tests/test_production_video_transition.py`

**Contract:** Tests must reproduce the actual failure classes without importing mutable `artifacts/` or raw Provider
output. The RED set must cover：compound primary camera motion、missing camera start/end、missing
camera-subject relation、missing open/close、screen-axis omission、moving endpoint translated to locked camera、
reserved `[Shot 2]`/cut-time text、same Shot action overload、generic `key=value` prompt reaching H3，以及
historical requirement/compiler payloads remaining reopenable。另以 sanitized adjacent-Shot fixtures 固化 v12 的
causal failures：character 无 bridge 出现/消失、产品从 absent 到已持有、holder/hand 无交接改变、推荐直接跳到
使用；同时固化 v13-style “holder transfer 已通过但 character entrance/exit 仍失败”，一个合法
`commercial_cut` 和一个喷用→结果但 performance 尚未评估的非等价 verdict。Conditioning oracles must also
separate incompatible-anchor forced snap/tail collapse from compatible FL2VA、I2VA first-only and a deliberate
settled endpoint hold。

**Implementation Notes:**

- Use synthetic, sanitized contract fixtures that encode the observed causal failures；do not copy raw prompts、
  private paths or Provider responses into tests。
- Separate authoring/transition failure、per-Shot readiness failure and compiler failure：unreachable adjacent state
  must block before compiler；incomplete Shot intent must block at readiness；H3-specific grammar conflict must
  return typed unsupported at compile。
- Add one positive oracle for locked camera and one for a single primary moving path plus stable tracking relation and
  explicit terminal motion state。
- Assert temporal ordering alone cannot satisfy causal reachability，and causal PASS cannot satisfy performance、
  lip-sync or selected-domain whole-video readability/pacing；Commercial `Hook Readability` remains a Commercial
  oracle，not a Shared Core requirement。
- Assert low tail motion alone is not a failure oracle：a requested settled close state may hold，while a scale/scene
  snap toward an unreachable last anchor must fail on compatibility plus boundary evidence。
- Preserve existing neutral compiler fixtures for Hailuo、Seedance and fake adapters。

**Acceptance:** New tests fail for the intended reasons against current code；the v12-style 4.500s/7.250s transitions
cannot pass through an order-only assertion；historical compatibility fixtures still pass before implementation。

**Verification:** Run the focused command above and capture the expected RED test names before editing production
code。

### Milestone 2: Add A Minimal Rich GenerationIntent And Stabilization Camera Contract

**Files:**

- Modify: `src/ai_video/production/video_requirement.py`
- Modify: `tests/test_production_video_requirement.py`
- Modify: `tests/test_planning_video_planner.py`

**Contract:** Add a versioned `GenerationIntent` branch that is rich enough for a model to perform rather than only
mechanically move。It retains the existing open/close、identity、scene、space、axis、subject action、motion envelope、
pacing and endpoint owners，and adds bounded typed projections for：

- `performance_intent`: trigger、visible response、gaze target、body/hand behavior and terminal performance state；
- `visual_treatment`: medium/look、palette/material treatment and prohibited visual drift；
- `lighting_intent`: motivated source、direction、exposure priority and continuity state；
- `ambience_intent`: explicit environment bed and action-bound foley cues；
- `dialogue_intent`: stable speaker ID、verbatim text、time window、on/off-screen state、response obligation and
  `lip_sync_required`；
- `music_intent`: explicit `none` or sealed instrumentation、tempo/rhythm and dynamics；
- `primary_camera_motion`: one v1 stabilization motion with kind、direction、amplitude、speed、start state and end
  state；
- `camera_subject_relation`: subject ID plus one stable relation such as fixed-frame、maintain-offset、follow、lead or
  reveal，with start/end relation。This relation constrains tracking and is not a second creative camera motion。

These structures are projections of approved Story/Scene/Shot facts，not new creative owners；Shot-level values carry
only the applicable state or override and must not silently rewrite a Scene-wide look、lighting or audio bed。They may
use bounded non-empty semantic text inside owned slots；do not turn film language into a single
closed global taxonomy。The v1 motion/relation enum is only the accepted H3 stabilization profile。New cinematic
grammar requires an additive contract/compiler version rather than silently broadening existing values。

`CameraEndpoint.start_framing/end_framing`、`AxisContinuity.camera_axis`、
`SpaceContinuity.screen_direction` and `SubjectAction` remain unique owners；the new structures do not duplicate
them。`CameraIntent.movement` remains historical/other-provider compatibility only。

**Implementation Notes:**

- Introduce `provider-neutral-generation-intent/2` and `provider-neutral-video-requirement/4` only when the complete
  pilot contract is present；projection `/1` and requirement `/1`–`/3` serializers must omit all new fields and
  preserve old hash fixtures bit-for-bit。Requirement `/4` is the single new rich-intent branch，not separate camera、
  audio or commercial variants。
- Reject two primary motions and contradictory primary/relation geometry structurally；do not infer motion from
  free-text camera verbs。
- `locked` requires `stationary -> settled`；moving paths may end `settled` or `continuing`。A primary truck/dolly
  may coexist with stable follow/maintain-offset relation when the relation does not add an independent path。
- Every prompt-richness projection carries explicit applicability：a Shot without dialogue uses an explicit empty/
  none boundary rather than fabricated speech；`audio_need=forbidden` requires explicit silent ambience/dialogue/
  music states；otherwise H3 readiness requires sealed ambience and explicit music intent。The compiler must never
  invent ambience or score from visible action。
- Only the selected pilot H3/T8 new-attempt lane must use `/4` before the empirical gate；other Provider migrations
  remain deferred。

**Acceptance:** Model validation rejects compound/contradictory camera values and missing prompt-richness owners；a
primary move plus stable tracking relation is accepted；new `/4` hashes deterministically；all historical serialized
payload/hash fixtures remain unchanged。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py -q
```

### Milestone 3: Add Pre-Generation Causal Transition Readiness

**Files:**

- Create: `src/ai_video/production/_video_intent_validation.py`
- Modify: `tests/test_production_video_intent_validation.py`
- Modify: `src/ai_video/production/video_transition.py`
- Modify: `tests/test_production_video_transition.py`
- Modify: `src/ai_video/planning/video_planner.py`
- Modify: `src/ai_video/quality_gates/shot_readiness_gate.py`
- Modify: `tests/test_planning_video_planner.py`
- Modify: `tests/test_shot_readiness_gate.py`

**Contract:** Readiness has three pure checks and must not collapse them：

1. **Per-Shot completeness:** generated video with `continuity_mode != none` requires typed open/close、subject
   action、performance、visual treatment、lighting、ambience/dialogue/music boundary、screen direction、axis、
   `primary_camera_motion`、`camera_subject_relation`、camera endpoints and exact positive duration。
2. **Intra-Shot conditioning compatibility:** FL2VA binds approved first/last anchor identities plus an explicit
   compatibility projection for subject scale、framing/composition、screen order/axis、camera path、character/prop
   state、action endpoint and available duration。The last anchor must be a reachable close state，not merely a desired
   image。Missing or incompatible evidence blocks before input upload；the caller may explicitly author a compatible
   last anchor or select I2VA，but Router/adapter不得在失败后自动 change lane、anchor、recipe or seed。
3. **Pairwise causal reachability:** every adjacent Shot binds a versioned `ContinuityTransitionPolicy` whose edge
   semantics is one of `direct_continuity`、`causal_ellipsis`、`scene_reset` or `commercial_cut`。For each applicable
   dimension，the policy binds source close projection、target open projection and one transition mode：`carry`、
   `visible_change` or `authorized_release`。`visible_change` requires a named bridge beat/action；
   `authorized_release` is legal only for the declared edge semantics。

The minimum v1 dimensions are character presence/entrance/exit、prop identity/holder/hand-contact/functional state、
action phase、gaze target、dialogue turn/response、screen motion/axis and audio bridge。人物出现/消失、关键产品从
absent 到 present、holder/hand 改变、`closed -> open -> ready-to-use -> used -> stowed` 不能仅凭相邻顺序或自由
文本通过。Missing、conflicting、unreachable or unauthorized release returns stable field-path diagnostics and zero
Router/compiler/Provider calls。

**Implementation Notes:**

- Replace `_typed_generation_intent_is_sufficient()` 的 “任一字段非 unspecified” semantics with the pure
  validation result；不要让 Planner 重建 Shot or Provider requirement。
- Version `ContinuityTransitionPolicy` additively；historical version `1` remains exact reopen/replay。Do not keep
  causal dimensions as an unrestricted `tuple[str, ...]` in the new branch。
- A direct edge defaults to carry unless a visible change is named。`causal_ellipsis` records omitted time and
  allowed state changes；`scene_reset` and `commercial_cut` release only explicitly listed dimensions。No caller may
  infer reset from prose or from a visually abrupt result。
- The Shot sequence owner must add a bridge beat when the required change is narratively essential。The compiler and
  transition validator cannot synthesize `recommend -> handoff -> receive -> open -> use -> effect` after authoring。
- Conditioning compatibility is approved semantic evidence，not an image-similarity score or a claim that matching
  pixels guarantee quality。It must distinguish a deliberate `settled` endpoint hold from forced snap/freeze caused by
  an unreachable last anchor。
- Readiness remains structural，不能声称 camera quality、prompt adherence、P6 或 HUMAN PASS。
- The validator is provider-neutral and pure；Production runtime不得 import or execute external Skill scripts。

**Acceptance:** Synthetic v12 edges at 4.500s and 7.250s and v13 holder-PASS/presence-FAIL edges produce typed STOP
before compiler；an incompatible FL2VA last anchor blocks while compatible same-scale FL2VA and explicit I2VA remain
valid distinct requests；spray→effect can pass causal order while performance remains separately unevaluated；a
declared commercial cut can release character presence while retaining product/brand obligations；complete rich
single-camera intent reaches the requirement projection without historical hash drift or side effects。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_intent_validation.py \
  tests/test_production_video_transition.py \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_errors.py -q
```

### Milestone 4: Compile Exact H3 Three-Field Prompt From Sealed Intent

**Files:**

- Create: `src/ai_video/production/_h3_prompt.py`
- Modify: `src/ai_video/production/video_compiler.py`
- Modify: `tests/test_production_h3_prompt.py`
- Modify: `tests/test_production_provider_neutral_adapters.py`

**Contract:** `_h3_prompt.py` is the sole H3 native grammar owner. It consumes an already selected、current
`ProviderNeutralVideoRequirement` and returns either exact prompt text or a typed unsupported result with stable field
paths。It must not select Provider/profile、modify requirement、invent Shot facts、fallback、read files、call Skill、
submit or write state。

The exact prompt has at most one mode-required reference instruction line，followed by exactly one each in order：

```text
integrated_multimodal_description:
overall_soundscape:
non_diegetic_music:
```

The visual field contains exactly one `[Shot 1]` and serializes only sealed scene/open/action/close、performance、
visual treatment、lighting、screen direction、axis、start framing、one primary camera motion、one compatible
camera-subject relation、end framing and terminal motion state。Reserved `[Shot 2]`、cut-time grammar、
transition/flash/xfade/retime instructions and unsealed secondary camera prose are rejected。

`overall_soundscape` serializes only sealed ambience、foley、dialogue and silence facts。`non_diegetic_music`
serializes the explicit `music_intent`，including explicit `none`。The compiler must not derive foley from an action、
invent a score、choose an emotional mood、add dialogue or rewrite verbatim text。If required H3 grammar lacks an
upstream owner，compilation returns typed unsupported rather than producing a safe-but-poor placeholder。

**Implementation Notes:**

- Keep `_compile_neutral_prompt()` for non-H3 adapters and historical compiler replay。
- Add an explicit native-prompt input/result seam to `compile_provider_video_request()`；do not detect H3 from
  provider name inside the generic compiler。
- NFC normalize once；prompt bytes and SHA must be deterministic for equivalent sealed input。
- Preserve stable speaker IDs and exact dialogue bytes；dialogue performance and lip-sync remain review concerns，not
  compiler claims。
- Do not copy the external `h3-video` Skill into runtime source；only encode the accepted three-field contract and
  repository-owned safety rules。

**Acceptance:** Complete `/4` intent deterministically produces rich official H3 grammar without creative additions；
performance、lighting、ambience、dialogue and music survive exact compilation；any incomplete/compound/multi-shot
input returns typed unsupported before external effect；neutral adapters retain exact prior output。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_h3_prompt.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_video_requirement.py -q
```

### Milestone 5: Route One Evidence-Backed Local H3 Pilot Lane Through The Shared Compiler

**Files:**

- Modify: `src/ai_video/production/comfy_video.py`
- Modify: `tests/test_production_comfy_video.py`
- Modify: `tests/test_production_local_h3_provider_family.py`

**Contract:** Only the Stock20 `ComfyUIVideoProvider` FL2VA quality new-attempt `compile_request()` is migrated before
empirical validation。It calls the shared H3 prompt compiler and binds exact returned bytes into existing
request/payload/hash lineage。It may not supply a handwritten prompt or fall back to `_compile_neutral_prompt()` after
H3 compilation fails。Other Local/Cloud H3 and T8 adapters，including Native Turbo，remain unchanged until
Milestone 8。

**Implementation Notes:**

- Advance only the selected Stock20 FL2VA compiler version `1 -> 2`。Capability/profile compiler contracts and tests
  must agree。Existing v1 compiled requests remain reopen/replay-only；do not relabel their hashes。
- Local H3 family delegation must preserve selected child identity and cannot reselect another child on unsupported。
- Workflow render functions continue binding `request.prompt_text` verbatim；no second adaptation is permitted at
  node-binding time。
- This lane is selected because the exact Qingyan handoff reconnaissance used Stock20 FL2VA and completed the required
  visible transfer without forced transition。Four-arm evidence shows compatible Stock20 and compatible Native Turbo
  both technical PASS，so there is no evidence-based reason to migrate both before the compiler hypothesis is tested。
- The current canonical profile/runtime commit drift must be resolved by running the exact pinned runtime or creating
  a separately versioned、reviewed profile；do not overwrite/reseal the existing profile in place。An upstream workflow
  or Turbo recipe upgrade is not a prerequisite unless a later isolated comparison supports it。

**Acceptance:** The pilot lane has exactly one sealed prompt path、conditioning compatibility preflight and exact
lineage；all non-pilot adapters retain their current bytes/versions；offline tests demonstrate no selection fallback、
anchor substitution or node-level rewrite。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_provider_neutral_adapters.py -q
```

### Milestone 6: Run Independent Drama And Commercial Empirical Gates

**Files / Artifacts:**

- Read/verify shared boundary: `docs/agent-primary-contract-matrix.md` (`Quality Gate Architecture Boundary`)
- Read/verify domain separation: `docs/superpowers/plans/2026-08-25-ai-video-quality-gate-architecture-separation.md`
- Read/verify Shared Core evidence: `docs/record_for_agent/2026-08-28-h3-causal-readiness-phase-a.md`
- Read/verify Commercial failure: `docs/record_for_agent/2026-08-28-h3-m6-causal-micro-sequence-gate-stop.md`
- Read/verify Commercial regression oracles:
  `docs/record_for_agent/2026-08-27-qingyan-v12-causal-recut-and-single-close.md` and
  `docs/record_for_agent/2026-08-27-qingyan-v13-causal-handoff-experiment.md`
- Required external Drama dependency, absent at this revision and not created by this plan:
  `docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md`
- Update the exact domain record after each future verdict；do not combine Drama and Commercial evidence in one
  artifact-level PASS。

**Authorization Boundary:** This plan revision performs no media action。Future M6-D / M6-C execution must satisfy
the then-current Provider/media rules。Strict-loopback Local ComfyUI may use the repository's current authorization
exemption，but exact identity、selected profile/workflow/binding、input/output provenance、unknown-outcome stop、
per-Shot Gate and no automatic cross-lane chaining remain mandatory。Remote/paid execution continues to require its
existing exact authorization、budget、egress、permit and recovery gates。A call allowed in one lane does not authorize
the other lane。

#### M6-D Drama Lane

**Precondition:** Do not author prompts、select a fixture or generate media until the independently accepted Drama
workflow/spec above owns exact Story/Scene/Character/Shot inputs、narrative rubric、stable requirement IDs、evidence
authority and whole-scene acceptance semantics。The current absence is a real `BLOCKED_BEFORE_MEDIA` condition，not
permission for this continuity plan to invent Drama truth。

**Fixture Contract:** The accepted Drama owner must provide one bounded dramatic scene with at least two persistent
characters and `2–3` generated Shots。The selected scene must expose，without forcing a specific plot：

- an established spatial relation and screen axis；
- one visible entrance、exit or motivated repositioning；
- at least one dialogue turn plus visible listening/reaction obligation；
- one relationship-, decision- or object-state change that must be causally readable；
- a terminal reaction、decision、payoff or continuation state that closes the scene beat。

The Drama owner selects the exact aspect ratio、resolution、cinematic reference/baseline、dialogue text、acting intent、
coverage and edit grammar。The continuity lane may validate those sealed facts but may not rewrite them into a product
demonstration、same-camera laboratory setup or generic `commercial_cut`。A shared requirement for continuity-critical
action may use direct continuity、causal ellipsis or scene reset only as explicitly sealed；shot/reverse-shot coverage
does not release eyeline、blocking、dialogue turn or emotional reaction obligations。

**Drama Findings:** Keep requirement-level verdicts separate：

- shared physical/perceptual continuity：identity、wardrobe、character/object state、space、axis、action phase、
  gaze/dialogue/motion/audio bridges、conditioning and camera endpoint；
- performance：body/face behavior、timing、listening/reaction、blocking、eyeline and dialogue/lip-sync；
- Drama-only narrative continuity from the accepted owner：motivation、relationship causality、decision consistency、
  conflict/stakes、emotional progression and applicable payoff/continuation intent；
- whole-scene readability and pacing against the selected Drama baseline。

Every generated Shot must pass the mandatory exact-byte per-Shot barrier before the next submit。The assembled exact
scene must receive uninterrupted `1.0x` full-speed/full-audio HUMAN verdict。Sampled frames、SSIM、decode PASS、scene
detection or technical continuity cannot substitute for any required human finding。

#### M6-C Commercial Lane

**Current Evidence:** The completed Qingyan `15.5s` micro-sequence remains HUMAN `FAIL` for watchability、commercial
quality baseline and assembly acceptance。Its `768x768` locked-anchor/locked-camera laboratory setup cannot be retried、
repaired or expanded into `30s` under the old verdict。Historical Shot technical PASS remains exact-byte technical
evidence only。

**Reopen Contract:** A future Commercial attempt requires an accepted Ecommerce package、Product Truth/claim lineage、
selected product/character/scene assets and an exact source-quality baseline。For Qingyan，the current comparison floor
is the exact `1344x768` raw set under `/home/reggie/电商图片/青颜/青颜视频_20260824/raw/`；a new attempt must preserve the
accepted format/composition intent and may not lower image fidelity、performance naturalness、camera/motion energy or
commercial readability merely to simplify anchor compatibility。The selected creative package，not this plan，owns
the exact product story and claims。

**Commercial Findings:** Keep requirement-level verdicts separate：

- shared physical/perceptual continuity：character/product presence、holder/hand/functional state、action phase、
  space/axis、camera endpoint、conditioning and sound bridge；
- performance、Dialogue Performance / Lip-sync and whole-video pacing；
- Ecommerce-only acceptance：Product Truth/claim correctness、Hook、product introduction/presentation、credible
  demonstration/proof、benefit hierarchy、CTA and brand closure；
- exact side-by-side source-quality baseline：resolution/composition、image fidelity、natural motion、acting and
  commercial viewing energy。Any required dimension below baseline is `FAIL` and cannot be averaged away。

Every generated Shot must pass the mandatory exact-byte per-Shot barrier before the next submit。Only after the bounded
Commercial micro-sequence passes shared continuity and Commercial HUMAN requirements may a new exact whole-ad candidate
be assembled and reviewed at uninterrupted `1.0x` full-speed/full-audio。A product-state PASS、technical Gate or
commercially readable still frame cannot substitute for whole-video acceptance。

#### Cross-Lane Decision Matrix

| Outcome | Required action | What remains valid |
| --- | --- | --- |
| Drama domain-only `FAIL` / `NOT_EVALUATED` | Stop M6-D and return to Drama owner；do not change Shared Core or Commercial rubric without shared evidence | An existing exact M6-C verdict remains scoped to its bytes/contracts |
| Commercial domain-only `FAIL` / `NOT_EVALUATED` | Stop M6-C and return to Ecommerce/creative owner；do not change Drama rubric | An existing exact M6-D verdict remains scoped to its bytes/contracts |
| Shared continuity `FAIL` in either lane | Return to the smallest Shared Core owner；any changed shared contract/compiler invalidates prior cross-domain qualification and requires both lanes to revalidate applicable shared requirements | Unchanged domain observations remain historical evidence only |
| One lane PASS, other lane not PASS | Record only that lane's development evidence；do not claim dual-domain support and do not begin M7–M9 | The passing lane may guide an isolated follow-up but cannot qualify the other lane |
| Both lanes PASS | Proceed to M7 only if productization is still justified | Exact Drama and Commercial HUMAN evidence remain separate；no Production/P6/Final Acceptance implication |

**Acceptance:** M6 completes only when one exact Drama scene and one exact Commercial whole-video artifact each have：

1. all applicable Shared Continuity findings `PASS`；
2. all required selected-domain findings `PASS` under their independent owners；
3. uninterrupted user `1.0x` full-speed/full-audio HUMAN PASS bound to exact SHA；
4. baseline comparison PASS for that domain；
5. no finding borrowed from or inferred by the other lane。

This first pair supports only the bounded dual-domain continuity hypothesis。It does not prove portfolio-level quality
reuse、Production candidate、P6、Final Acceptance、publication、commercial effectiveness or Drama audience success。

**Verification:** For each lane，verify exact hash/media probe、selected domain-profile identity、project-local per-Shot
evidence、pairwise `1.0x` findings、baseline comparison and whole-video human verdict。Any recomposition/re-encode/
audio replacement produces a new SHA and invalidates the previous whole-video verdict。Before M7，verify both lane
records against the unchanged Shared Core commit/compiler/profile identity；do not merge their verdicts into one score。

### Milestone 7: Productize Exact Pairwise Media Evidence And Honest Post Treatment

**Files:**

- Modify: `src/ai_video/production/video_transition.py`
- Modify: `src/ai_video/production/review.py`
- Modify: `src/ai_video/production/continuity_evaluator.py`
- Modify: `src/ai_video/production/composition.py`
- Modify: `tests/test_production_video_transition.py`
- Modify: `tests/test_production_review.py`
- Modify: `tests/test_production_continuity_evaluator.py`
- Modify: `tests/test_production_composition.py`

**Contract:** Every adjacent generated-video pair that claims continuity must bind one current
`ContinuityTransitionPolicy` and generic generated-Shot review evidence that simultaneously identifies exact source
and target artifact bytes plus source terminal and target opening sample windows。Evidence covers the applicable
typed dimensions from Milestone 3：character presence/entrance/exit、prop identity/holder/hand/state、action phase、
dialogue/gaze/audio bridge、screen axis/action direction、subject scale/framing、camera direction/relation and camera
start/end motion state。Any missing/stale/mismatched/`FAIL`/`NOT_EVALUATED` required dimension blocks a
continuity-claiming composition。

**Implementation Notes:**

- Extend the generic `ContinuityEvaluationIntent` / `GeneratedShotContinuityEvidence` owner in `review.py` rather
  than repurposing qualification-specific `SourceBoundaryHumanDecisionV1`。Qualification source closure remains
  unchanged and does not become the generic composition edge owner。
- Keep requirement-level results；do not create a generic aggregate score。Automated evidence may measure technical
  state，but semantic causality、performance and readability remain human where the evaluator cannot establish them。
- Separate **evidence eligibility** from **transition execution**：raw source/target continuity is adjudicated before
  any seam-masking transform。A final composition is then reviewed on its own exact SHA for readability and pacing。
- `xfade`、dissolve、flash、padding、retime and interpolation are not globally forbidden。They are legal only when
  declared by an applicable edge/use：montage、dream/time jump、scene reset、commercial cut、deterministic graphic
  treatment，or stylistic treatment after required causal continuity already passes。They may not synthesize a
  missing handoff、hide a character/prop state jump or upgrade `FAIL`/`NOT_EVALUATED` to PASS。
- Domain-specific edit semantics require the selected domain owner：`commercial_cut` can release only sealed
  Commercial dimensions；Drama shot/reverse-shot、narrative ellipsis、scene transition or montage obligations come
  from the accepted Drama profile。Neither profile may reinterpret the other's release rules。
- Direct action continuity defaults to a zero-duration hard cut or other evidence-neutral cut。A reset/ellipsis cannot
  be inferred after seeing failed media，and post treatment always creates new artifact identity requiring review。
- Tail motion is interpreted against the sealed endpoint：a requested settled hold is legal；low optical flow alone
  cannot fail it。A forced scene/scale snap、unreachable-anchor absorption or premature velocity collapse against a
  continuing endpoint remains FAIL。
- Do not attempt to inspect arbitrary shell scripts heuristically。Accepted outputs must pass through canonical
  `CompositionSpec` / `ResolvedTimeline`; artifact-specific FFmpeg assemblies remain local previews and cannot claim
  system-level continuity acceptance。

**Acceptance:** Mismatched moving-to-locked boundary、missing prop holder/state、unsettled camera endpoint、implicit
character appearance/disappearance and a transform used as continuity repair all block。A complete direct pair
resolves deterministically；an explicit dream/montage/scene reset/commercial cut may use its declared treatment without
claiming released dimensions passed continuity。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_transition.py \
  tests/test_production_review.py \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_composition.py \
  tests/test_shot_continuity_source_review.py -q
```

### Milestone 8: Expand The Proven Compiler And Retire New-Profile Dual Authoring

**Files:**

- Modify: `src/ai_video/production/minimax_h3.py`
- Modify: `src/ai_video/production/comfy_t8_video.py`
- Modify: `src/ai_video/production/comfy_t8_turbo_video.py`
- Modify: `tests/test_production_minimax_h3.py`
- Modify: `tests/test_production_comfy_video.py`
- Modify: `tests/test_production_comfy_t8_video.py`
- Modify: `tests/test_production_comfy_t8_turbo_video.py`
- Modify: `tests/test_production_local_h3_provider_family.py`
- Modify: `scripts/prepare_shot_continuity_p0.py`
- Modify: `src/ai_video/production/shot_continuity_m0_operator.py`
- Modify: `tests/test_prepare_shot_continuity_p0.py`
- Modify: `tests/test_shot_continuity_m0_operator.py`
- Modify: `tests/test_video_compiler_c4_qualification.py`
- Modify: `tests/test_shot_continuity_m0_reprepare.py`
- Create: `workflows/qualification/minimax_h3_fl2va_rainy_station_source_v2_profile.json`
- Do not modify: `workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json`

**Contract:** Only after Milestone 6 records separate Drama and Commercial empirical PASS for the unchanged Shared
Core，remaining Local/Cloud H3 and T8 new-attempt adapters may adopt the same sealed H3 compiler one by one。One lane
PASS cannot authorize dual-domain adapter expansion。Each adapter advances compiler identity exactly once，keeps
historical compiled requests bit-for-bit reopenable and cannot fallback after unsupported。New qualification profile
preparation derives its prompt from the same sealed semantic intent；existing v1 profile and prompt SHA remain
immutable historical evidence。

**Implementation Notes:**

- Migrate and verify each adapter independently；a passing pilot does not waive adapter-specific capability/profile
  and exact payload tests。
- Replace manual semantic/prompt double entry only for newly prepared qualification profiles；historical replay keeps
  exact embedded prompts。
- Qualification remains local、explicit、one-submit/no-retry/no-fallback。This milestone is offline and does not
  reseal runtime state or generate media。

**Acceptance:** Every migrated new-attempt H3/T8 adapter has one prompt owner and exact lineage；unmigrated historical
branches are replay-only；a new qualification profile cannot disagree with its semantic intent。

**Verification:** Run all adapter-specific tests plus：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_prepare_shot_continuity_p0.py \
  tests/test_shot_continuity_m0_operator.py \
  tests/test_video_compiler_c4_qualification.py \
  tests/test_shot_continuity_m0_reprepare.py -q
```

### Milestone 9: Align Routing, Run Exact Acceptance And Independent Review

**Files:**

- Modify: `.agent/harness/policy.yaml`
- Modify: `tests/test_agent_harness.py`
- Modify: `.agent/context/control-plane-playbook.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md` only after implementation evidence changes phase status

**Contract:** New `_h3_prompt.py`、`_video_intent_validation.py` and their tests must map to the existing
`provider_neutral_video_requirement`、`production_video_provider`、`shot_readiness_gate` and
`shot_continuity_p0` mandatory checks as applicable。Harness receipt must bind a non-empty exact staged snapshot or
exact commit range；unrelated dirty/untracked files must not enter the execution tree。

Routing docs must preserve one AI-VIDEO owner and state：`open-video` advises coverage、Shot purpose and bridge-Shot
need；`hell-grind-aigc-skill` advises semantic continuity and causal state；`video-shotcraft` advises camera/shot
language、camera-subject relation、action/gaze/sound bridge and pacing for both generated Shot authoring and
deterministic composition；all advice is compressed into the one approved Shot / `GenerationIntent` / transition
contract；`h3-video` advises only H3 grammar adaptation。No Skill runs in Production runtime or owns Provider、state or
review truth。

Domain routing remains explicit：the independently accepted Drama workflow/spec owns Drama story、motivation、
relationship、dialogue semantics、emotion and payoff rubric；`ecommerce-ad-workflow` owns Ecommerce Product Truth、
claims、Hook、presentation/demo/proof、CTA and brand closure。Shared continuity evidence may be consumed by either lane，
but neither domain owner may write or reinterpret the other's verdict。

**Implementation Notes:**

- Run focused tests first，then policy-required full combination and `python -m scripts.architecture_gate check`。
- Use one native `reviewer_xhigh` after the final diff because this changes core prompt、continuity、cross-module
  contracts and old-path retirement。Blocking fixes receive same-tier scoped re-review。
- Keep `AGENTS.md` thin；detailed Creative Skill routing remains in the playbook，surface owner/check mapping remains
  in the contract matrix。Do not modify external Skill packages in this implementation slice。
- Stage only exact task-owned paths with `git add <specific-files>`；do not stage `.codex/config.toml`、`artifacts/`
  or unrelated existing spec/plan files。
- Commit the implementation at a stable checkpoint；do not push or release without a separate request。

**Acceptance:** All mandatory checks pass on explainable exact state；review has no blocking issue；fresh receipt
passes scope、policy、hash and freshness verification；final architecture search finds no alternate H3 new-attempt
prompt path or second continuity owner；docs claim only behavior proven by code/tests and exact human evidence。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_h3_prompt.py \
  tests/test_production_video_intent_validation.py \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py \
  tests/test_shot_readiness_gate.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_comfy_video.py \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_comfy_t8_native_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_prepare_shot_continuity_p0.py \
  tests/test_video_compiler_c4_qualification.py \
  tests/test_production_video_transition.py \
  tests/test_production_review.py \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_composition.py \
  tests/test_shot_continuity_source_review.py -q
python -m scripts.architecture_gate check
git diff --check
make harness-inspect
make harness-verify
```

## Execution Order And Stop Conditions

Execution is deliberately gated：

| Phase | Required work | Exit / stop rule |
| --- | --- | --- |
| R0 — Commercial/shared reconnaissance | Complete；four-arm attribution + one handoff Shot + v13 30s recut + M6-C causal assembly | Supports incompatible-anchor attribution and visible holder transfer；Qingyan HUMAN watchability/commercial baseline FAIL；does not prove Drama or authorize productization |
| A — Minimum offline hypothesis | Milestones 1–5 only | Proves exact typed causal intent plus compatible conditioning can reach one pilot adapter prompt；does not prove model quality |
| B-D0 — Drama owner prerequisite | Accepted Drama spec、exact accepted/sealed fixture and baseline、无`BLOCKER`的sealed authoring package、verified current execution gates and exact evidence path | 任一documentation identity/acceptance缺失，或current execution gates / exact evidence path未验证时，仍为`BLOCKED_BEFORE_MEDIA`；documentation candidate由用户或Spec委托的primary agent按exact fail-closed contract判定，this plan must not invent Drama acceptance |
| B-D — Drama empirical lane | One bounded dramatic scene plus exact whole-scene HUMAN verdict | All applicable shared + Drama findings and Drama baseline must PASS；otherwise stop only this lane unless Shared Core failed |
| B-C — Commercial empirical lane | Reopen only through a new accepted Commercial attempt；current Qingyan M6-C is HUMAN FAIL | All applicable shared + Commercial findings and source-quality baseline must PASS；old assembly cannot be repaired or expanded |
| B-X — Dual-domain closure | Reopen both exact lane records against unchanged Shared Core identity | Both lanes PASS independently；one lane cannot qualify the other |
| C — Productize dual-domain proven behavior | Milestones 7–9 | Add generic post-media enforcement、remaining adapters/qualification、routing/Harness only after B-X PASS |

Current status is B-D0 `PASS`（accepted v1 semantic spec + accepted v2 delegated-authority overlay +
accepted/sealed fixture + baseline selection + authoring-package v3 + independently reviewed and accepted current
execution-gate/exact-evidence-path）、B-D
`NOT_EVALUATED`、B-C `HUMAN_FAIL` and B-X `FAIL`。M7 pairwise
post-media productization、M8 adapter/qualification expansion and M9 routing/Harness completion remain explicitly
deferred。The existing v12/v13/M6-C bytes remain Commercial/shared regression evidence；none can be promoted to Drama
or dual-domain PASS by relabeling technical receipts。

The local baseline-reference acquisition recorded in
`docs/record_for_agent/2026-08-29-drama-baseline-reference-shot-01-gate-stop.md` is not M6-D execution。Current user has
accepted both its exact Shot 1 reference component and the exact baseline-selection record；the new authoring-package v3
candidate was independently adjudicated `CONFIRM` under the accepted v2 delegated-authority overlay and is sealed by
`docs/superpowers/artifacts/drama/b-d0/authoring-package/key-at-the-waiting-room-v3.accepted.json`。This clears the
package exact-acceptance blocker only；it did not authorize retry, additional Shots, M6-D, P6 or Final Acceptance。
The acceptance content first entered history at commit `02b03f65e09f0135c71bb8ee4e1ff1653fdf5167`；the later
task-owned finalization checkpoint only refreshes exact closure evidence after an unrelated concurrent HEAD advance。

The execution-gate/evidence-path prerequisite is now independently accepted and sealed by
`docs/superpowers/artifacts/drama/b-d0/execution-gate/key-at-the-waiting-room-v1.accepted.json`。它固定current
callable readiness/Provider lifecycle与Agent-controlled Development evidence paths，包括attempt-qualified exact
Shot/pair/assembly SHAs、explicit project-local `video-analysis` raw evidence、requirement-level HUMAN verdict、
sequential stop、identity invalidation、unknown-outcome stop与cross-lane no-inheritance。它不声称typed Drama Product
Runtime、Gate 2、M6-D、P6或Final Acceptance已实现；M6-D仍须作为独立 empirical slice 另行进入。

M6-D已在2026-08-29由current user明确启动；fresh Shot 01最初在canonical Planner entry前停止。历史blocker evidence位于
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-execution-preflight.json`，SHA-256为
`8c7031f42a068b953a75a7f7b0bb9dfd5611d516c0821657dc34d94723683d5c`。当时没有Project/Registry-selected
Drama Character/Scene/Shot revision/content hashes，故当时不存在canonical `VideoPlanningRequest`；historical baseline
test helper或in-memory copies不能替代该authority。

Current user随后明确授权实现canonical Drama Project/Registry materialization seam。Current runtime采用additive
pre-generation target contract：`generated_video` Shot必须显式携带唯一empty `VIDEO` target role，不能注册placeholder
asset；candidate activation仍由existing committer把该role替换为exact generated MP4 binding。Provider-neutral
`GenerationOperation.TEXT_TO_VIDEO`只在无media reference且continuity不要求exact/reference anchor时可得到proposed
plan，避免把Character/Scene semantic context伪装成media evidence。Run-local driver从accepted package/fixture的exact
Git bytes投影typed artifacts，仅调用`ProductionStateCommitter.bootstrap_initial_state()`；canonical state与Planner evidence
位于`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/production-project/`及
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-canonical-materialization.json`，后者SHA-256为
`75be2e494e44b5b253d730f9c9daca366806e09209c7e5e5e231c014a1b09f71`。Selected Project content hash为
`940f0ceee3148ba1d4dab4a5b7bcbc2adc3229c5964f1705149bec1e9d14dfc1`，empty Registry identity为
`13a9404d3ec6bb3de0ec00871cd22dd5ca861ca8ea413fdfe13ea145e6c2ec1b`，Shot 01 request hash为
`92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f`，verified projection hash为
`9481519d2b4929e6abd9b0826cc5731ea54f60526ec414ffa07279d32f0a57fb`。Exact bootstrap replay已验证14个
Production files零写入。

Historical pre-generation graph checkpoint曾停在`PROVIDER_PROFILE_NATIVE_PROMPT_AND_EXACT_REQUEST_NOT_SELECTED`。Implementation commit
`6a5bbbf65d175eb58e1fbe2e6753a2965705b8d8`新增显式`GENERATION_TARGET` projection与in-lock exact-current
guard；run-local driver只经`ProductionStateCommitter.bootstrap_dependency_graph()`与
`upgrade_manifest_schema("2.7")`激活graph `761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1`。
15个creative states全部`FRESH`，唯一Shot 01 target为无applied media evidence、无blocker的`STALE` ready frontier。
Exact evidence位于`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-pre-generation-graph.json`
（SHA-256 `4bd08f0a6ce3a8e666816f264a1a7a20acfd3897b4ce58f264bd4f17fb4f4115`），accepted checkpoint为
`docs/superpowers/artifacts/drama/b-d0/execution-gate/key-at-the-waiting-room-v2.accepted.json`。候选
`minimax-h3-t8-t2va-quality-v1` profile另要求ComfyUI commit
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`，current clean checkout为
`e01fb4c56b7a88149d469b99cbbfe3223d715054`，即使上游readiness未来解除也仍须重新通过exact runtime
identity preflight；该inspection不是Router decision，且当前未选择该profile。Source-audio当前只保留从sealed
Shot facts推导的`GENERATED + KEEP` authoring-intent proposal，因Provider未selected而没有accepted SourceAudioPolicy
或resolved request binding。该historical checkpoint没有选择或改变fixture/baseline，没有启动ComfyUI、编写Provider-native prompt、持久化request、submit、
生成media或调用`video-analysis`。

Historical stop `CANONICAL_SHOT_01_EXECUTION_INTENT_INCOMPLETE` 已由versioned additive overlay prerequisite解除，
没有覆盖其request `92e6de89a72730da3beb58638dd54c637cad5162aab94a3259d3413a9a50931f`、requirement
`d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81`或unsupported evidence。Accepted overlay
`docs/superpowers/artifacts/drama/b-d0/execution-intent/key-at-the-waiting-room-shot-01-v1.accepted.json`（SHA-256
`8b50b61b152b59542fc4521c870cc060b9b6469fc18db5e3a14248cf05de7efd`）显式拥有当前Shot所需execution choices；
strict canonical reopen生成新request `01c329aa22b898521d0611bd4fbcfcbba912babb81b4ce85a88582985704fe7c`、
verified projection `f2292b67f3616a5b4757c6c3e45301b971230bb59a3b683207d8a6d6cb412b1d`、requirement
`d234cd95b712ca8d966132d28c6ee15a49831b412305b795c8c8eb9a2491b34d`与prompt
`3676c9998a63e7ddc024faff7d18f07f5e48722046ee7193201f490ee57c750d`。Prompt audit为exactly three lines、exact
dialogue once、explicit Chinese tag、`non_diegetic_music: none`，且无raw JSON、Story/Scene/future bookkeeping、opaque
canonical identity、abstract objective或`unspecified`。Accepted evidence位于
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-authoring-to-request-accepted-v1.json`
（SHA-256 `1e38b731b31b4866720d5b80bfb2dd40da04ebe56dea8656f3d7219d15298cb6`）。

Provider/profile/runtime/exact-request readiness prerequisite已通过current canonical Router执行。显式quality-first candidate为
`comfy-local-h3-t8` / `minimax-h3-t8-t2va-quality-v1` / profile
`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`，required runtime identity当前exact match且checkout
clean；但sealed requirement要求fixed `5.0s`，selected profile只声明`frame_count=124`，Router因此返回
`blocked_capability / PROVIDER_CAPABILITY_DENIED`并且不产生`ProviderBoundVideoRequest`。Blocked evidence位于
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot-01-provider-profile-runtime-request-readiness-blocked-v1.json`
（SHA-256 `f214645086e11c41d698190ac0ff4418278da9c02aae6ca1605b964d304b2cb1`），封存 envelope 位于
`docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/key-at-the-waiting-room-shot-01-v1.blocked.json`。
Current blocker为`FIXED_5S_REQUIREMENT_NOT_EXPRESSIBLE_BY_SELECTED_T8_PROFILE`；`M6-D`仍保持
`NOT_EVALUATED / STOP_BEFORE_SUBMIT`，`next_shot_submit_allowed=false`。没有exact request preview、SourceAudio binding、
Provider preflight、permit、submit或per-Shot media Gate。

Stop immediately and report rather than expanding scope when：

- historical hashes cannot remain bit-for-bit；
- the selected H3 capability cannot express the sealed intent without inventing facts；
- implementation requires a new Provider、fallback、schema rewrite rather than the versioned additive branch；
- another writer owns any target file；
- the selected lane lacks its accepted domain owner、sealed profile/rubric、approved fixture or exact baseline；
- a required causal pairwise boundary remains `FAIL` or `NOT_EVALUATED`；
- an FL2VA last anchor lacks approved same-scale/reachable endpoint compatibility；
- the output falls below its selected domain's image fidelity、performance、camera/motion、readability or pacing
  baseline even when causal state is technically reachable；
- a proposed verdict borrows a requirement、PASS or release rule from the other domain lane；
- one lane passes while the other remains `FAIL` / `NOT_EVALUATED` and the next action would claim dual-domain support；
- a Shared Core change is proposed after one lane PASS without invalidating and replanning both lanes' shared
  revalidation；
- Provider outcome is unknown；
- the requested empirical action lacks exact model/input/budget/egress/permit authorization。

## Rollback And Completion Boundary

- Before any live/media work，Phase A can be rolled back by reverting the new requirement branch、causal readiness、
  shared H3 compiler and pilot adapter routing together；do not leave a new-attempt adapter on a partial contract。
- Milestones 7–9 are separate post-evidence changes and must not be pre-implemented or activated behind an assumption
  that either domain lane or dual-domain Phase B will pass。
- Historical compiler/profile branches remain available only for exact reopen/replay，not new attempt creation。
- A domain-only requirement/rubric change invalidates only that lane unless shared contracts changed；a Shared Core、
  compiler、conditioning or generic continuity-evidence change invalidates the applicable shared findings in both
  lanes。
- A prior Drama or Commercial PASS remains exact development evidence only；it cannot be copied into the other lane or
  used to bypass its missing owner/profile/baseline。
- Phase A completion requires focused tests and historical compatibility，not a quality claim。Full Plan completion
  requires separate exact Drama and Commercial HUMAN evidence、B-X identity reconciliation plus Phase C
  code/tests/docs/policy agreement、fresh Harness receipt、same-tier independent review and no alternate H3
  new-attempt prompt path。
- A technical implementation PASS does not complete the empirical decision gate；a HUMAN PASS does not imply
  Production/P6/Final Acceptance。
