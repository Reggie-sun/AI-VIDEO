# AI-VIDEO Shot-to-H3 Continuity Enforcement Implementation Plan

**Goal:** 先用最小可验证链证明：approved Shot sequence 的跨 Shot 因果状态经唯一 sealed
`GenerationIntent`、pairwise causal transition contract 与 deterministic H3 compiler 后，能减少怪运镜、
compound motion、intent drift 以及人物/产品状态跳变；真实 HUMAN evidence 成立后，才扩大到全 adapter、
qualification、composition enforcement 与 Harness 收口。

**Scope:** Provider-neutral Shot semantic intent、camera/subject relation、pre-generation pairwise causal
readiness、一个 evidence-backed Local H3 pilot adapter 的 exact prompt compilation、符合当前 H3 frame 下限的
`10.333–15.500s` causal micro-sequence、第一条 exact 30s whole-video HUMAN verdict，以及只有 empirical
evidence 支持后才执行的 remaining adapter、qualification、post-media pairwise evidence、composition 与
Harness 收口。

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
pairwise readiness -> exact H3 three-field prompt -> bounded real-media experiment -> HUMAN verdict`。四臂实验已把
forced scale transition / terminal snap 的主要原因收敛到 incompatible last anchor；随后 one-Shot causal handoff
又证明 compatible anchors 与明确动作链可完成可见 holder transfer，但 30s recut 仍在 `4.500s`、`9.667s` 和
`19.458s` 因 character presence jump 失败。只有包含 entrance/exit 与 holder/action state 的完整因果链获得真实
evidence 后，才把同一 contract 扩大到 remaining adapters、qualification、post-media evidence 与 canonical
composition。

**Compatibility:** Historical `provider-neutral-video-requirement/1`–`/3`、existing compiled request、resolved
request、activation scope、compiler/profile hash 和 qualification profile 必须 bit-for-bit reopen/replay；新的
camera contract 采用 additive versioned branch，只用于 new attempts。旧 compiler/profile 不得被静默重解释，
也不得通过自动 migration 改写 existing Manifest、receipt 或 artifact identity。

**Out of Scope:** 新 camera Skill、Provider selection/fallback、未经单独授权的 live/paid submit 或媒体生成、
自动 repair、renderer/timeline replacement、新 P6 writer、新 aggregate quality score、训练或微调、将
development HUMAN PASS 升级为 Production/P6/Final Acceptance、全面重写任何 external Skill，以及清理历史
artifact-specific scripts。

**Acceptance Criteria:**

- H3/T8 pilot new attempt 缺少完整 open/close、action、performance、visual treatment、lighting、audio/music
  boundary、axis、camera path、camera-subject relation 或 camera endpoint 时在 Provider effect 前 typed BLOCKED；
- continuity-sensitive adjacent Shots 缺少可验证的 character presence、prop holder/hand/state、action phase、
  gaze/dialogue/motion bridge，或未声明合法 ellipsis/reset/commercial cut 时，在 compiler/Provider 前 typed
  BLOCKED；
- FL2VA first/last anchors 缺少同尺度/同构图可达性、duration-bounded endpoint compatibility 或 approved
  compatibility evidence 时，在 upload/Provider effect 前 typed BLOCKED；不得在失败后自动换 anchor、lane 或
  recipe；
- 一个 AI-VIDEO Shot 只能编译一个 `[Shot 1]` 和一个 `primary_camera_motion`；允许一个不构成第二 creative
  motion 的 stable `camera_subject_relation`，禁止 internal cut time 和 `[Shot 2]`；
- exact submitted H3 prompt 由 sealed requirement 确定性生成，并包含唯一且有序的
  `integrated_multimodal_description`、`overall_soundscape`、`non_diegetic_music`；
- pilot H3/T8 adapter 不再调用 generic neutral prompt 作为 new-attempt native grammar；其他 adapters 在首轮
  empirical gate 前保持不变；
- 先以一个符合当前 H3 `124 frames @ 24 fps` 下限的 `10.333–15.500s`、`2–3` generated-Shot causal
  micro-sequence（可带固定 surrounding context）取得 requirement-level HUMAN evidence；失败即回到责任层，
  不继续建设 Milestones 7–9；
- post processing 不得创造或伪造 continuity PASS。`xfade`、dissolve、retime、interpolation、padding 可在
  typed montage、dream/time jump、scene reset、commercial cut 或已通过边界上的明确艺术/节奏用途合法存在，
  但不能替代缺失的 causal state change，且变换后的新 SHA 必须重新验收；
- 第一条 30s HUMAN PASS 绑定 exact final SHA、完整 `1.0x` 播放、每个 pairwise boundary、Dialogue
  Performance / Lip-sync 与 Hook Readability 的分离 verdict；任何重编码或修复后必须重新验收新 SHA。

**Verification:** Phase A 使用 strict RED-GREEN focused tests、historical hash/reopen fixtures 与 pilot adapter
offline tests；Phase B 只在单独授权下执行 `10.333–15.500s` causal micro-sequence 和 exact 30s `1.0x` human playback；
Phase C 通过 empirical decision gate 后才运行 remaining adapter、composition/P6 regression、Architecture
Gate、policy-routed Harness exact staged snapshot receipt 与一次 `reviewer_xhigh` independent review。Offline
acceptance 不执行 Provider、ComfyUI 或媒体生成。

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
- `artifacts/qingyan-miao-ad-20260827-v12/authoring/authoring-contract.md`
- `artifacts/qingyan-miao-ad-20260827-v12/ecommerce-package.json`
- `artifacts/qingyan-miao-ad-20260827-v12/review/final-gate.md`

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
micro-sequence 或 30s HUMAN gate，也不授权继续 M7–M9。

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
| Quality / acceptance | P6 + exact human evidence | analyzer/technical PASS 不得冒充 HUMAN PASS 或 Final Acceptance |
| Dialogue Performance / Lip-sync | per-Shot media review + human evidence | 与 causal edge 分离；edge 只拥有 speaker turn、gaze/response 与 sound bridge obligation |
| Hook Readability / whole-ad pacing | exact whole-video human evidence | technical presence/timing 可自动检查；可读性、说服力与节奏不由 aggregate score 代判 |

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
  lip-sync、Hook Readability or whole-video pacing。
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

### Milestone 6: Run The Empirical Decision Gate Before More Infrastructure

**Files / Artifacts:**

- Read/verify first: `artifacts/qingyan-miao-ad-20260827-v12/final/青颜_苗家腋下止汗完整广告_30s_9x16_v12.mp4`
- Read/verify: `artifacts/qingyan-miao-ad-20260827-v12/authoring/authoring-contract.md`
- Read/verify: `artifacts/qingyan-miao-ad-20260827-v12/ecommerce-package.json`
- Read/verify: `artifacts/qingyan-miao-ad-20260827-v12/review/final-gate.md`
- Read/verify: `docs/record_for_agent/2026-08-27-h3-conditioning-attribution-gate-stop.md`
- Read/verify: `docs/record_for_agent/2026-08-27-qingyan-v13-causal-handoff-experiment.md`
- Modify before new media to preserve the new boundary-level human evidence:
  `docs/record_for_agent/2026-08-27-qingyan-v12-causal-recut-and-single-close.md`
- Create only after the new exact empirical verdict:
  `docs/record_for_agent/2026-08-27-qingyan-shot-to-h3-causal-pilot.md`

**Authorization Boundary:** The completed one-submit v13 reconnaissance was separately authorized and is exhausted；
it does not authorize another Provider/ComfyUI submit、new media、paid effect or recomposition。Any new micro-sequence
or 30s artifact requires exact task-scoped authorization and all Provider/media gates。The existing evidence is
sufficient to classify v12/v13 pairwise failures；it is not permission to regenerate them。

**Completed Reconnaissance:** The single generated handoff Shot technical PASS proves explicit visible transfer plus
compatible anchors can execute on Stock20。The exact 30s recut is still causal FAIL because holder continuity does not
cover character entrance/exit。The prompt was handwritten and the experiment anchors were not Production-registered，
so this evidence does not satisfy Milestones 4–5 or either empirical exit gate below。Do not repeat the same holder-only
experiment。

**Contract:** Execute two empirical steps in order：

1. **Causal micro-sequence:** author `10.333–15.500s` / `2–3` generated H3 Shots, optionally bounded by fixed accepted
   context，around `visible elder entrance/presence -> recommend/show -> handoff/receive -> explicit elder exit or
   authorized release -> open/use -> effect`，using the new per-Shot、conditioning and pairwise contracts。The exact
   duration follows the current H3 minimum of `124 frames @ 24 fps` per generated Shot；do not claim an `8–12s / 3–4
   generated-Shot` test or trim away the state transitions being tested。Keep Provider/profile、approved assets、
   reference scope and other controllable variables fixed。Each generated Shot still passes the mandatory per-Shot
   post-media Gate before the next submit。
2. **30s assembly:** only after the micro-sequence obtains causal HUMAN PASS，assemble or generate the bounded 30s
   candidate and obtain an uninterrupted `1.0x` full-speed/full-audio whole-video verdict。

The rubric emits separate requirement-level findings：

- causal state reachability：character presence、product holder/hand/state、action endpoint/start、dialogue/gaze/
  motion/audio bridge；
- conditioning compatibility：first/last scale/composition、reachable endpoint、absence of forced snap/scene-scale
  transition；
- generated camera：single primary motion、camera-subject relation、endpoint stability、absence of compound drift；
- semantic intent adherence and performance naturalness；
- Dialogue Performance / Lip-sync；
- Hook Readability and whole-ad pacing。

Do not collapse these into one score。For the motivating boundaries，4.500s and 7.250s are causal FAIL；13.250s may
pass causal order while performance stays `NOT_EVALUATED`；17.042s separates semantic comprehensibility from
cast/camera continuity；24.333s may be an authorized commercial cut while pacing remains human-first。

**Decision Gate:**

- Micro-sequence causal HUMAN FAIL：stop and diagnose asset/Shot contract/compiler/adapter/model responsibility；do
  not begin Milestones 7–9。
- Micro-sequence causal PASS but performance/camera FAIL：run at most the separately authorized isolated comparison
  needed to test that failure；do not broaden infrastructure。
- Micro-sequence PASS and 30s HUMAN FAIL：classify exact spans and return to the smallest owner；do not treat the code
  slice as a quality success。
- 30s HUMAN PASS：record only exact development artifact evidence，then proceed to Milestone 7 if productization is
  still justified。

**Acceptance:** The micro-sequence first obtains uninterrupted user causal `HUMAN_PASS` for every presence/holder/
action boundary。Then one exact 30s artifact has uninterrupted user `HUMAN_PASS`，all required causal boundaries PASS，and
Dialogue Performance / Lip-sync、Hook Readability/pacing are separately evaluated。This is development evidence only；
it does not imply Production candidate、P6、Final Acceptance、publication or commercial effectiveness。

**Verification:** Exact hash/media probe、project-local per-Shot evidence、pairwise `1.0x` review and whole-video human
verdict。Any recomposition/re-encode produces a new SHA and invalidates the previous whole-video verdict。

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

**Contract:** Only after Milestone 6 records the required empirical PASS，remaining Local/Cloud H3 and T8 new-attempt
adapters may adopt the same sealed H3 compiler one by one。Each adapter advances compiler identity exactly once，keeps
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
| R0 — Empirical reconnaissance | Complete；four-arm attribution + one handoff Shot + v13 30s recut | Supports incompatible-anchor attribution and visible holder transfer；30s presence FAIL；does not validate compiler or authorize productization |
| A — Minimum offline hypothesis | Milestones 1–5 only | Proves exact typed causal intent plus compatible conditioning can reach one pilot adapter prompt；does not prove model quality |
| B1 — Causal micro-sequence | Milestone 6 step 1 | `10.333–15.500s` / `2–3` generated H3 Shots must obtain HUMAN causal PASS before any new 30s attempt；FAIL returns to the smallest owner and stops M7–M9 |
| B2 — First 30s verdict | Milestone 6 step 2 | Exact 30s HUMAN PASS is required before infrastructure expansion |
| C — Productize proven behavior | Milestones 7–9 | Add generic post-media enforcement、remaining adapters/qualification、routing/Harness only after Phase B PASS |

Therefore，before the first 30s HUMAN PASS，the mandatory milestones are M1–M5 plus the feasible
`10.333–15.500s` micro-sequence gate in M6。M7 pairwise post-media productization、M8 adapter/qualification expansion
and M9 routing/Harness completion are explicitly deferred。The existing v12 bytes fail the 4.500s and 7.250s causal
boundaries；the v13 reconnaissance fixes holder transfer but still fails character presence at 4.500s、9.667s and
19.458s。Neither can be promoted to the first 30s HUMAN PASS by re-labeling technical receipts。

Stop immediately and report rather than expanding scope when：

- historical hashes cannot remain bit-for-bit；
- the selected H3 capability cannot express the sealed intent without inventing facts；
- implementation requires a new Provider、fallback、schema rewrite rather than the versioned additive branch；
- another writer owns any target file；
- a required causal pairwise boundary remains `FAIL` or `NOT_EVALUATED`；
- an FL2VA last anchor lacks approved same-scale/reachable endpoint compatibility；
- the micro-sequence does not improve causal reachability or generated camera behavior；
- Provider outcome is unknown；
- the requested empirical action lacks exact model/input/budget/egress/permit authorization。

## Rollback And Completion Boundary

- Before any live/media work，Phase A can be rolled back by reverting the new requirement branch、causal readiness、
  shared H3 compiler and pilot adapter routing together；do not leave a new-attempt adapter on a partial contract。
- Milestones 7–9 are separate post-evidence changes and must not be pre-implemented or activated behind an assumption
  that Phase B will pass。
- Historical compiler/profile branches remain available only for exact reopen/replay，not new attempt creation。
- Phase A completion requires focused tests and historical compatibility，not a quality claim。Full Plan completion
  requires Phase B exact human evidence plus Phase C code/tests/docs/policy agreement、fresh Harness receipt、same-tier
  independent review and no alternate H3 new-attempt prompt path。
- A technical implementation PASS does not complete the empirical decision gate；a HUMAN PASS does not imply
  Production/P6/Final Acceptance。
