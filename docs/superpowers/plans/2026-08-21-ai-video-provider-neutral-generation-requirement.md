# AI-VIDEO Provider-Neutral Generation Requirement Implementation Plan

## Status

Implemented and offline-accepted at commit
`007e99cb1d79f9c2b91a909b15db1f9360f65236`，该commit也是current cached
`origin/main`；尚未release。T1–T9的source、tests、Harness routing、canonical docs与old-path
retirement均已完成。Exact implementation snapshot的passing receipt为
`.agent/harness/runs/20260820T223106358086Z/receipt.json`，覆盖Harness、video Provider、shared
requirement、Router、Planner与Architecture checks。

本Plan下方的task decomposition保留为implementation history；其中`Implemented work`描述已由
上述commit完成的offline slice。T10 Local H3 regression后来在独立授权下执行，cloud/paid live
仍未执行。本Plan及既有receipt均不授权新的Provider/ComfyUI/network/credential调用、媒体生成、
quality acceptance、Final Acceptance或release。

Local `main` commit `15ef1d510a59cc9d46445b1fafff2ac2b34a1473`后来additive加入
`comfy-local-h3-t8` Quality/Turbo family。2026-08-21的docs correction将current three-method
family标为partial，并把provider-name-scoped完整stateless local pass-through列为remaining target；
同时补齐Local H3、Seedance、Hailuo、MiniMax H3与future Providers的coexistence/assembly boundary。
该correction不扩大T1–T9 durable lifecycle，也不以历史receipt替代target implementation仍需的fresh
verification。

## Goal and Boundary

按最小vertical slice实现：

```text
pure requirement model/builder
  -> planner projection
  -> explicit Provider candidate snapshots
  -> Router exact Provider/profile/capability mapping
  -> fake adapter compiler contract
  -> Local H3 families / cloud H3 / Hailuo / Seedance offline mappings
  -> exact Provider lookup + explicit local/remote service assembly
  -> tests/Harness and old-path retirement
  -> separately authorized Local H3 live acceptance
```

Single owner：`VideoPlanner`唯一派生neutral requirement；Shot Router唯一产生Provider/profile/capability
selection；`VideoProviderRegistry`只做exact-name lookup；explicit caller按sealed `execution_kind`注入
exact Provider；selected Adapter唯一编译/执行Provider grammar；existing `ProductionStateCommitter`
唯一持久化lifecycle。

Old paths to remove：run-local prompt construction、orchestration direct provider-bound request construction、Adapter implicit creative decision。

Unchanged：Shot、Registry、Manifest、committer、permit、recovery、Dependency Graph、`ResolvedTimeline`、HyperFrames、Review/Repair、Final Acceptance、Legacy CLI/Manifest。

## Implemented Change Surface

以下是commit `007e99c`实际采用的ownership surface；表内边界不授权新的修改：

| Area | Implemented files | Purpose |
| --- | --- | --- |
| Pure schema | `src/ai_video/production/video_requirement.py` | strict nested neutral models、hashing、forbidden fields；no IO |
| Planner | `src/ai_video/planning/_planner_models.py`, `video_planner.py` | request/plan v3、typed generation intent、single builder、verified boundary、freshness |
| Router | `src/ai_video/production/shot_router.py` | verified requirement projection、exact selection projection、provider-bound seal；no planning import |
| Core lifecycle DTO | `src/ai_video/production/video.py` | compiler protocol/result、request `/5`、resolved `/6`、activation scope `/4` while preserving all historical branches |
| Fake | `src/ai_video/production/video_fake.py` | deterministic compiled/unsupported acceptance |
| Local H3 | `src/ai_video/production/comfy_video.py` and exact profile-owned tests | offline compiler mapping only；sealed workflows unchanged unless separately approved |
| Local H3 T8 family | `comfy_t8_video.py`, `comfy_t8_turbo_video.py`, `local_h3_provider_family.py` | current aggregation/compile/resolve；remaining target是same-name full stateless local pass-through |
| Cloud adapters | `src/ai_video/production/minimax_h3.py`, `minimax_hailuo.py`, `seedance.py` | offline deterministic compiler mappings；no network |
| Tests | focused planning/router/video/provider test files | RED/GREEN, compatibility, no-side-effect, retirement |
| Harness/docs | `.agent/harness/policy.yaml`, Harness tests, canonical docs | exact changed-path routing and verified runtime truth only after implementation |

Exact file ownership must be rechecked before dispatch。若存在same-file writer overlap，implementation开始前停止并由用户决定ownership/顺序；disjoint files按current repository rules继续。

## Contract Checkpoint Before Code

Implementation parent必须在写code前记录并核对：

- **Problem boundary:** neutral plan semantics currently stop before provider-bound request construction。
- **Single owner:** Planner derives requirement；Router selects；Adapter compiles；committer persists。
- **Old path:** direct `VideoGenerationRequest.create()` in production orchestration and run-local prompt builders。
- **Unchanged contract:** request `/1`–`/4`、resolved `/2`–`/5`、activation scope `/1`–`/3` historical hashes/reopen、P8 lifecycle、P5 desired fingerprint owner、no fallback。
- **Focused first command:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py \
  tests/test_errors.py -q
```

## Vertical Slice Tasks

### T1 — Pure requirement model and seal

**Goal:** 建立cycle-neutral strict models，不接Router/Adapter。

Implemented work：

- add `ProviderNeutralVideoRequirement`及cohesive nested identity/state/continuity/action/camera/reference/output/audio/quality models；
- implement canonical ordering、NFC validation、requirement ID/hash、recursive forbidden-field validation；
- bind exact source request、Shot、intent、asset和Review identities；
- no Provider/model/profile/workflow/prompt/payload/Skill/fallback/lifecycle fields；
- add pure import/no-IO/no-environment tests。

RED cases first：same semantic input determinism、diagnostic ID exclusion、stale/tampered hash、unordered identity、forbidden nested field、missing evidence binding。

Exit：pure focused command passes；no current Planner/Router behavior changed。

### T2 — Planning request/plan v3 projection and one-truth migration

**Goal:** `VideoPlanner`成为唯一requirement builder，plan内不再重复serialized generation truth。

Implemented work：

- preserve historical `VideoPlanningRequest` / plan v2 hash fixtures but reject them for new attempts；
- add required v3 typed generation-intent projection for open/close state、identity/scene/space/axis、action/motion/pacing、camera endpoints and objective capability needs；
- require explicit `UNSPECIFIED` values and block/review them by mode；never infer missing semantics from prose；
- emit `VideoGenerationPlan video-planner/3` only from request v3 with required nested requirement；
- move serialized generation/continuity/motion/required-role/capability data into requirement；
- provide bounded read-only compatibility properties only；
- update `require_current_video_plan()` freshness checks to verify request -> requirement -> plan chain；
- return a cycle-neutral `VerifiedGenerationRequirementProjection` containing requirement plus verified plan/source/target hashes；do not expose plan type to Router；
- update proposed readiness compatibility tests without implementing `ShotReadinessGate` itself；
- prove `PROPOSED` still means eligible only, not quality/activation acceptance。

RED cases first：v2 request rejected for new attempt、typed `UNSPECIFIED` policy、prose-only semantics blocked、duplicate serialized truth rejected、manually substituted requirement blocked、Shot/intent/Review/asset mutation changes hashes、same request identical plan。

Exit：planner focused tests and existing STOP spies pass；Router/Provider counts remain zero on stale/blocked plan。

### T3 — Router requirement mapping and provider-bound projection

**Goal:** Router从embedded requirement做exact capability matching并输出prompt-free `ProviderBoundVideoRequest`。

Implemented work：

- consume only the cycle-neutral verified requirement projection；`shot_router.py` must not import `ai_video.planning` or `VideoGenerationPlan`；
- add one explicit exhaustive mapping from requirement enums/semantic roles to Router mode/roles；
- validate exact verified lineage、requirement、Shot、Registry and evidence freshness；
- include requirement hash in semantic routing hash contribution；
- preserve audit hash policy/capability ownership；
- create sealed provider-bound projection with exact selection、bindings、output、base pointers和compiler contract；
- preserve single exact capability/no fallback behavior；
- keepProvider candidate snapshots explicit；Registry lookup不得成为pre-selection、ranking或fallback；
- bindselected `provider_name`、`execution_kind`与`billing_kind` so explicit assembly can inject the exact local or remote adapter without reselecting；
- reject unexpressible native-control/role/output needs before Adapter when capability metadata already proves denial。

RED cases first：all enum values map once or typed block、reference count excludes first/last、capability/profile mismatch、local/remote authorization、same input deterministic provider-bound hash、Provider change leaves requirement hash unchanged。

Exit：Router tests pass；no adapter/Provider/lifecycle call occurs on blocked decisions。

### T4 — Fake adapter compiler contract

**Goal:** 稳定Adapter API和unsupported semantics，再接real adapters。

Implemented work：

- define `compile_request(provider_bound, requirement)` pure protocol；
- define discriminated `CompiledProviderVideoRequest | ProviderRequirementUnsupported`；
- add compiler ID/version/hash、request `/5`、resolved request `/6` and activation scope `/4` lifecycle lineage；
- preserve historical request `/1`–`/4`、resolved request `/2`–`/5` and activation scope `/1`–`/3` hash fixtures byte-for-byte；
- select new schema branches only when complete lineage fields are present；resolved `/5` remains hard-cut and must not be reused；
- fake compiler supports an explicit small capability matrix and returns typed unsupported for every other requirement；
- ensure compile cannot select Provider、mutate requirement、drop fields、fallback、create permit或submit。

RED cases first：compiled determinism、unsupported field paths/reasons、no partial prompt/payload、compiler version changes only compiled/request fingerprint、resolved `/5` collision rejection、all legacy hash fixtures unchanged、zero side effects。

Exit：fake adapter -> existing resolve/preview/lifecycle tests pass offline；old direct creation remains only in marked legacy fixtures。

### T5 — Local H3 families and cloud H3 offline mappings

**Goal:** 对current sealed H3 capability实现deterministic compiler，不修改workflow或live behavior。

Implemented work：

- Local H3 `fl2va`: first frame required、last frame optional、no reference slots、exact geometry/24fps/native audio/seed semantics；
- Local H3 T8 family: Quality/Turbo保持同一`provider_name`下的distinct exact capabilities；current family合并capabilities并委托compile/resolve；remaining target按durable identity委托完整local seam，selected child仍实现具体action；
- keep base and additive quality profile seals unchanged unless a separate profile migration is explicitly approved；
- cloud H3: T2V fixed output/no refs/no seed/no negative prompt；
- convert only approved neutral semantics to reviewed grammar；
- return typed unsupported for native controls or semantic reference roles the lane cannot express；
- add architecture search proving Candidate 1 prompt/locked-camera sentence is absent from generic source/fixtures。

Exit：offline H3 tests pass；no ComfyUI、network、credential或media generation。

### T6 — Hailuo offline mapping

**Goal:** 保留Hailuo 2.3 adaptive I2V truth和strict role boundary。

Implemented work：

- exactly one first frame；no last/reference role；adaptive `768P`、141 frames@24fps、MP4/no native audio；
- compile semantic action/camera/pacing without claiming native control；
- block fixed pixel claims、required close endpoint、native audio、seed/negative prompt or reference roles；
- preserve current submit/poll/fetch/Paid Gate and existing live evidence；no new call。

Exit：Hailuo offline mapping and legacy lifecycle tests pass；no paid preview/permit/POST。

### T7 — Seedance offline mappings

**Goal:** 对exact dated profile按mode映射semantic roles，保持Ark materialization和paid gates。

Implemented work：

- I2V first/last role、R2V image refs、edit/extend video/audio refs分别映射；
- enforce 2.0 Mini count/measurement/duration/output/audio limits and model-specific capability differences；
- keep `SeedanceAssetReferenceResolver` as existing Ark identity/materialization owner；requirement不保存`asset://`；
- compile provider payload fields mechanically，unsupported不降级mode或切换Model；
- retain explicit `generate_audio` and existing payload omission rules；
- no pricing/Endpoint claim without implementation-day current snapshot。

Exit：Seedance offline/fake transport tests pass；no credential、Ark call、cost或activation。

### T8 — Old-path retirement, invalidation and compatibility

**Goal:** 只有新链路能创建new production attempts，同时历史证据可reopen/replay。

Implemented work：

- replace production direct request constructors with Planner -> requirement -> Router -> compiler；
- remove run-local prompt builders and adapter creative defaults；
- keep explicit historical `/1`–`/4` fixture/reopen seam，reject them for new attempt creation；
- add requirement/provider-bound/compiler contributions to existing desired generation fingerprint；
- prove precise P5 invalidation for Shot/asset/Provider/compiler changes and no unrelated blanket stale；
- verify exact replay、unknown outcome、permit、activation、recovery contracts unchanged；
- update canonical docs only with actually verified behavior。

Exit：architecture tests find no alternate production path；historical hashes unchanged；new request `/5` -> resolved `/6` -> activation scope `/4` path completes fake lifecycle only。

### T9 — Harness routing and final offline acceptance

**Goal:** 对exact staged snapshot完成policy-routed acceptance。

Implemented work：

- add `src/ai_video/production/video_requirement.py` and its tests to `production_video_provider` routing；
- because Planner and Router change，existing `video_planning` and `production_shot_router` categories must also route the shared requirement/focused checks；
- update Harness tests for overlapping categories and exact check IDs；
- run focused matrix、Production lifecycle regressions、Architecture Gate、`git diff --check`；
- stage only task-owned files，run `make harness-inspect` then `make harness-verify`；
- self-verify receipt，commit task-owned files，then verify exact commit range when required by final integration policy。

Exit：fresh receipt integrity/policy/snapshot checks pass；independent reviewer verdict has no blocker。

### T10 — Separately authorized Local H3 live acceptance

**Executed later under separate authorization.** T1–T9 accepted后，Local H3 initial technical
regression及后续一次用户授权的motion-continuity repair已分别完成；exact lineage、调用计数、
artifact hash与human verdict记录在
`docs/record_for_agent/2026-08-21-local-h3-readiness-seed-live-regression.md`。这些runtime
evidence不属于T1–T9 offline acceptance，也不授权future submit。

Executed boundary：

- exactly one Local H3 compiled request `/5` / resolved `/6` unless user separately expands scope；
- use current sealed additive quality profile and approved source assets；
- Candidate 1 baseline只作为regression oracle：`runs/c2-alice-local-h3-quality-candidate-1-20260821/output/alice-c2-local-h3-quality-candidate-1.mp4`，SHA-256 `2b02881d81b1226ab90e9791a472be7b6f02ef1b8584e5b2e1fe7d4050773de8`；不得生成Candidate 2/3；
- verify requirement -> Router -> compiler -> request lineage、loopback-only execution、lifecycle/reopen/replay；
- measure actual output with `ffprobe` and project-local `video-analysis`，并由human明确GO/NO-GO；
- technical/live proof不自动成为universal subjective quality acceptance。

Cloud/paid live remains another separately authorized task with full Paid Provider Gate。

### T11 — Multi-Provider coexistence clarification and regression

**Docs implemented in this correction；full family assembly与pure executable regression remain pending separate code scope.**

Required contract：

- one `VideoProviderRegistry` may contain `comfy-local-h3-t8`、`seedance`、`minimax_hailuo`、
  `minimax_h3` and future distinct-name Providers；
- exact lookup returns the exact injected object；duplicate exact name fails closed；
- Registry does not select、rank、inspect runtime or fallback；
- `VideoGenerationService` receives one exact injected Provider and does not query Registry；
- local family snapshots cannot contain remote Provider variants；
- Local H3 target family is the sole `comfy-local-h3-t8` Registry entry and delegates the complete local seam
  by durable identity，while selected child implements concrete actions；
- current three-method family is partial and cannot yet satisfy that Registry-to-Service assembly；
- all tests remainpure/no-network/no-Provider-call。

Future regression target：extend an existing provider-neutral/registry test file rather than create a second
catalog or coordinator. The test must be added to an actually executed Harness check `argv`；path mapping alone
is insufficient。

## Requirements-to-Tasks Traceability

| Requirement | Tasks | Primary tests |
| --- | --- | --- |
| one embedded requirement truth | T1–T2 | model seal、duplicate rejection、determinism |
| exact freshness/evidence identity | T1–T3 | mutation matrix、stale STOP |
| Router selection ownership/no fallback | T3 | capability/policy/authorization blocked decisions |
| adapter compile/unsupported contract | T4 | fake compiler discriminated results、zero effects |
| H3/Hailuo/Seedance differences | T5–T7 | provider-specific offline matrices |
| distinct-name Provider coexistence and exact assembly boundary | T3, T11 | Registry exact lookup/duplicate rejection、zero-call pure regression |
| request/resolved/scope fingerprint and P5 invalidation | T4, T8 | all legacy hash fixtures、new `/5`/`/6`/`/4` branches、precise closure |
| old path retirement | T8 | import/constructor/search/spy tests |
| unchanged lifecycle owners | T8–T9 | state/recovery/paid/dependency suites |
| exact Harness evidence | T9 | Harness inspect/verify/receipt |
| live evidence separation | T10 | separate authorized execution record only |

## Focused Test Matrix

| Test group | Must prove | Must not do |
| --- | --- | --- |
| Requirement model | strict schema、hash、canonical order、forbidden fields、exact evidence | IO、Provider imports、quality verdict |
| Planner | request/plan v3 typed projection、single derivation、nesting、verified envelope、freshness、STOP、determinism | Provider/profile selection、prose inference |
| Router | exhaustive projection、exact capability/profile、role counts、no fallback | prompt creation、state write |
| Provider coexistence | distinct names coexist、exact lookup、sealed execution kind、duplicate rejection | ranking、fallback、runtime inspection、Provider calls |
| Fake compiler | compiled/unsupported union、no mutation、lineage、legacy hash compatibility | network、permit、submit |
| Local/cloud H3 | exact role/output/seed/audio grammar boundary | ComfyUI/API call、generic Candidate 1 prompt |
| Hailuo | adaptive geometry、first-frame-only、unsupported close/reference/audio | paid preview/POST |
| Seedance | mode/reference/media/output/audio matrix、Ark identity boundary | secret/Assets API/submit |
| P5/lifecycle | desired fingerprint、precise invalidation、replay/recovery | second graph/writer/timeline |
| Architecture | import direction、single builder/compiler、retired call sites | baseline refresh hiding debt |

## Exact Verification Commands

以下是implementation使用并由passing Harness snapshot覆盖的verification commands；后续重验仍使用
repository-standard `python -m pytest`，不得用裸`pytest`。

### Pure model and Planner

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py \
  tests/test_errors.py -q
```

### Router projection

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_planning_video_planner.py \
  tests/test_production_shot_router.py \
  tests/test_production_video.py \
  tests/test_errors.py -q
```

### Fake adapter and lifecycle DTO compatibility

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_production_video.py \
  tests/test_production_video_fake.py \
  tests/test_production_video_state_recovery.py -q
```

### H3 families/Hailuo/Seedance offline mappings

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_video.py \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_minimax_hailuo.py \
  tests/test_production_seedance.py \
  tests/test_production_video.py -q
```

### Paid/lifecycle/dependency invariants

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_paid_provider_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

### Architecture and exact snapshot

```bash
python -m pytest -p no:cacheprovider \
  tests/test_architecture_gate.py \
  tests/test_architecture_gate_cli.py -q
python -m scripts.architecture_gate check
git diff --check
make harness-inspect
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
```

若final acceptance使用commit range：

```bash
make harness-verify-range BASE_REF=<verified-base-commit>
make harness-receipt RECEIPT=<fresh-range-receipt-path>
```

## Harness Changed-Path Routing

`.agent/harness/policy.yaml`已在同一implementation commit中加入以下changed-path routing：

| Changed paths | Required categories/checks |
| --- | --- |
| `src/ai_video/production/video_requirement.py`, `video.py`, `video_fake.py`, provider adapters and related tests | `production_video_provider_tests` + `task_architecture_gate` |
| `src/ai_video/planning/**`, planner tests | `video_planner_tests` + shared requirement/compiler focused check + `task_architecture_gate` |
| `src/ai_video/production/shot_router.py`, router tests | `production_shot_router_tests` + shared requirement/compiler focused check + `task_architecture_gate` |
| `.agent/harness/policy.yaml` / Harness tests | `harness_tests` plus every category matched by the same exact staged delta |
| canonical docs | `documentation` plus always-on `scope_diff_check`；docs不得代替code tests |

建议新增一个focused check `provider_neutral_video_requirement_tests`，其argv覆盖requirement、Planner、Router、fake compiler和typed errors；然后将该check同时加入`production_video_provider`、`production_shot_router`与`video_planning`的`check_ids`。现有更广的category checks继续运行，不能由focused check替代。

## Acceptance Lane Separation

### Fake/offline acceptance — T1–T9 default

可以证明：schema、determinism、freshness、capability mapping、payload projection、unsupported、legacy hash compatibility、P5 invalidation、lifecycle regression和old-path retirement。

不能证明：Provider account access、current pricing、network、billing、real media、visual quality、human GO或Final Acceptance。

### Local H3 live proof — T10 executed separately

Initial loopback-only technical regression及后续一次明确授权的motion-continuity repair已完成；两次
均保留exact profile、current assets、fresh runtime evidence、`ffprobe`与human review边界，且未命名
为Candidate 2/3。该结果不外推为universal quality acceptance，也不授权新的live submit。

### Cloud/paid live proof — separate future plan

必须另获exact Provider/model/input/budget/egress authorization，并重新验证credential reference、pricing、Endpoint、durable intent、one-use permit、unknown-outcome recovery。Hailuo/Seedance历史success或offline tests不授权新调用。

## Review Plan

Implementation review使用native named `reviewer`，至少检查：

- requirement是否真的是plan内唯一generation truth；
- Router是否仍独占selection且无fallback；
- Registry是否只做exact lookup、distinct-name Providers是否可并列、Service是否只消费exact injected Provider；
- Local H3 current partial/target full-seam边界是否准确；target family是否仅在same-name local
  children内委托且不吸收remote Providers、global selection或durable lifecycle；
- Adapter是否只表达、不重创作/降级；
- legacy request/resolved/activation-scope hashes是否精确保持，且new `/5`/`/6`/`/4` branches无version collision；
- tests是否覆盖真实old paths和semantic unsupported，而不只是happy path；
- P5/Manifest/committer/permit/recovery/timeline/Review ownership是否未漂移；
- fake/offline/live claims是否严格分层。

Reviewer必须输出`Verdict`、`Blocking issues`、`Non-blocking concerns`、file/test evidence和minimal follow-up。Parent必须复核重要claims和final diff。

## Rollback and Recovery

- T1–T7未进入durable lifecycle时，按task-owned commits反向撤销；不得保留双builder/双request path。
- T8切换new-attempt entry后，rollback必须整组恢复pre-slice code；historical `/1`–`/4` evidence始终可reopen。
- 任何已经durable begin的`/5` attempt只走existing explicit recovery；不得down-convert、blind retry或删除complete orphan evidence。
- T10 live失败按existing lifecycle记录known-no-effect、failed或outcome-unknown；不得因rollback重试Provider。

## Deferred and Explicitly Unauthorised

- `ShotReadinessGate` implementation、Shot Quality Gate、subjective quality automation；
- Provider ranking/fallback、multi-candidate generation、Candidate 2/3；
- global automatic Provider catalog、candidate discovery或Registry-to-Service coordinator；
- new Manifest/Registry layout、second writer/resolver/timeline/renderer；
- Local H3 live、Hailuo/Seedance/cloud paid live、billing settlement；
- push、release、publication或remote protection changes。

完成T1–T9只代表offline implementation acceptance，不代表live、quality、activation或Final Acceptance。用户再次授权前不得开始任何implementation task。
