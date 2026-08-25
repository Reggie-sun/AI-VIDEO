# Qingyan Ecommerce Post-Media Gate Repair Plan

**Goal:** 补齐青颜广告从 generated Shot candidate 到 whole-ad Final Acceptance 的 post-media 质量闭环，使失败镜头不能被继续生成、静帧替代或手工拼接掩盖。

**Scope:** Generated Shot commercial review、逐 Shot 同步 stop barrier、Whole-ad Ecommerce Gate 2、P6 `SEMANTIC` evidence bridge、canonical composition/render handoff，以及两阶段真实媒体 pilot。

**Contract Surfaces:** `CompiledAdCreativeHandoff`、`ResolvedVideoGenerationRequest`、`VideoGenerationService.validate_once()`、video candidate lifecycle、`QaPolicy`、`ReviewEvidence`/`ReviewReceipt`、`UniversalQaGateResult`、`CompositionSpec`、`ResolvedTimeline`、HyperFrames、`ProductionStateCommitter`。

**Invariants:** `ProductionStateCommitter` 仍是唯一 durable writer；`ResolvedTimeline` 仍是唯一 timing owner；HyperFrames 仍是 default renderer；Gate 不选择 Provider、不自动 retry/repair/activate；任一 required `FAIL`/`NOT_EVALUATED`/stale/unknown outcome 均 fail closed；Final Acceptance 仍只能由 existing P6 lifecycle 产生。

**Current / Target Behavior:** 当前 authoring 和 deterministic handoff 很强，但真实 Shot MP4、整片语义与手工成片旁路未被同一生命周期约束。目标行为是：exact commercial requirements 进入生成请求；candidate validation 持久化并裁决 post-media evidence；只有 PASS Shot 才能激活且允许下一 Shot；whole-ad Gate 2 通过 existing P6 `SEMANTIC` evidence/receipt 进入 Final Acceptance。

**Compatibility:** 现有非 Ecommerce 请求、Legacy `0.1.x`、非 commercial video attempts、旧 `QaPolicy` 和既有 Manifest 必须保持可读可执行。新增 commercial candidate checkpoint 采用 additive schema migration；不得原地猜测或改写旧 evidence。

**Out of Scope:** 新 Provider、新 CLI、新 dependency、第二 Manifest writer、第二 timeline/renderer、自动批量 retry、自动 Final Acceptance、市场效果预测，以及本计划修订阶段的任何 Provider 调用或媒体生成。

**Acceptance Criteria:** Negative artifact 能稳定被 requirement-level evidence 拒绝；每个 failed/unreviewed Shot 阻止后续 submit；Gate 2 的 PASS 被 exact P6 semantic receipt 持久化；canonical render provenance 完整；真实 pilot 经人工 A/B 后才允许扩 batch。

**Verification:** Focused pytest、schema/compatibility tests、Documentation Contract Gate、Architecture Gate、Harness exact staged/commit-range receipt，以及 normal-speed human media review。

## Revision Decisions

本修订版相对初稿锁定四项结构性决定：

1. 不创建平行于 P6 的第二套 durable whole-ad evidence lifecycle。Gate 2 的结果必须投影为 existing `ReviewEvidence(layer=QaLayer.SEMANTIC)`，并由 `ProductionStateCommitter.begin_review()`、`run_review_analysis()`、`record_review_receipt()` 与 `record_final_acceptance()` 管理。
2. Generated Shot commercial review 复用 `VideoGenerationService.validate_once() -> ProductionStateCommitter.prepare_video_activation_candidate()` seam，并仿照现有 `checkpoint_generated_shot_continuity()` 建立 sibling durable checkpoint。它发生在 candidate activation 前，不在 Provider adapter、FFmpeg 脚本或后置批处理里补审。
3. `composition.py` 和 `hyperframes.py` 不作为默认修改目标。现有 `compile_ad_creative_handoff() -> CompositionSpec -> resolve_composition() -> HyperFramesAdapter.render()` 已是 canonical path；本修复通过 coordinator 和 integration tests 消费它们。只有 RED test 证明现有 public contract 无法绑定 accepted Shot bytes 时，才另立 scoped change。
4. 不使用未经校准的全片 optical-flow 总分或任意 freeze 秒数作为 universal quality truth。Technical motion 复用 existing `frozen_required_motion`、window strategy 和 frame diversity；人物互动、动作完成、包装一致性与广告连贯性由 requirement-level evaluator/human evidence 判断。

## Problem Boundary

前置 `ecommerce-ad-workflow` G0–G7、`AdQCReport.ready` 和 `AdCreativeReviewReport.is_ready` 只证明 authoring readiness 与 sealed handoff integrity，不能证明生成后 MP4 中真的存在：

- 苗家女孩与老人有效互动。
- 老人自然推荐产品、女孩承接卖点和 CTA。
- 产品在计划时间窗出现且包装一致。
- 手持/使用动作没有 extra hands、穿模、flat overlay 或错误瓶型。
- required-motion Shot 真实运动而非静帧、clone freeze 或无意义 zoom。
- 全片按照问题—推荐—使用—效果—CTA 的广告弧连贯播放。

当前 P6 `SEMANTIC` 只要求 generic `semantic_match`，还不能 type-enforce exact Ecommerce profile、requirements 与 coverage。因此 single repair boundary 是：

```text
authoring truth
  -> generated candidate commercial evidence
  -> canonical accepted Shot set
  -> canonical render
  -> Universal Gate 1
  -> Ecommerce Gate 2
  -> existing P6 SEMANTIC receipt
  -> existing Final Acceptance
```

## Evidence Baselines

以下文件只用于人工 A/B，不得硬编码到 Runtime、tests 或 policy：

- Positive comparison: `/home/reggie/电商图片/青颜/青颜视频_20260825_miaozu/青颜_苗家女孩与老人_30s连续口播广告_candidate.mp4`
- Negative regression: `/home/reggie/vscode_folder/AI-VIDEO/artifacts/qingyan-miao-ad-20260825/final/青颜_苗家女孩T8动态广告_28s_9x16.mp4`

Positive comparison 不是 golden PASS。它仍可能在包装小字、claim、lip-sync 或连续性上得到 `FAIL`/`NOT_EVALUATED`。Negative regression 必须至少暴露：老人互动缺失、产品推荐口播缺失、required product-use beat 未进入成片、大量静态替代，以及缺少 canonical render/P6 binding。

## Target Ownership

| Concern | Canonical owner | Repair rule |
| --- | --- | --- |
| Product/claim/copy intent | Ecommerce authoring package + `AdCreativePlan` | 不扩展为 media verdict |
| Commercial Shot requirements | `CommercialExecutionProjection` + sealed acceptance profile | 绑定 exact plan/projection/Shot |
| Generated candidate validation | Existing video candidate lifecycle | 新 commercial checkpoint 是 sibling helper，不是新 writer |
| Whole-ad hard/universal checks | `UniversalQualityGateCoordinator` | Gate 1 PASS/current 才能进入 Gate 2 |
| Whole-ad Ecommerce adjudication | Pure Ecommerce Gate 2 | 逐 requirement 输出，不持久化 state |
| Durable semantic receipt | Existing P6 review lifecycle | Gate 2 evidence进入 `QaLayer.SEMANTIC` |
| Composition/timing/render | `CompositionSpec` / `ResolvedTimeline` / HyperFrames | 不新增旁路 |
| Activation/final acceptance | `ProductionStateCommitter` | 只有 existing committer 可写 |

## File Map

### New focused modules

- `src/ai_video/production/domain_acceptance.py`
  - 定义 generic `DomainAcceptancePolicy`，供 `QaPolicy` 绑定 exact domain/profile/required requirement IDs/evidence contract。
  - 不包含 Ecommerce 业务判断，不写 state。
- `src/ai_video/production/ecommerce_media_acceptance.py`
  - 定义 sealed Ecommerce profile、Shot/whole-ad requirement、finding、evidence payload 与 pure adjudication。
  - 不调用 Provider、renderer、committer 或 filesystem。
- `src/ai_video/production/_state_commit_video_commercial.py`
  - 仿照 `_state_commit_video_continuity.py`，在 held generated-video FD 上建立 durable intent/evidence checkpoint，并返回 exact reopened evidence。
  - 只由 existing video candidate mixin 调用，不形成 public writer。
- `src/ai_video/production/ecommerce_quality_gate.py`
  - 实现 explicit Gate 2 coordinator；消费 current Gate 1 result、sealed profile、exact render context 与 requirement evidence。
  - 输出 typed Gate result 和可进入 P6 的 `ReviewEvidence`，不自行落盘。
- `src/ai_video/production/ecommerce_ad_coordinator.py`
  - 显式、顺序地消费 `CompiledAdCreativeHandoff` 和 existing service APIs。
  - 负责 stop ordering，不复制 Provider、candidate、composition、timeline、render 或 P6 logic。

### Existing modules with bounded changes

- `src/ai_video/production/video.py`
  - 为 `ResolvedVideoGenerationRequest` 增加 optional sealed commercial acceptance binding。
- `src/ai_video/production/commercial_execution.py`
  - 从 exact `CommercialExecutionProjection` 和 selected profile 投影 per-Shot requirement binding；不执行生成。
- `src/ai_video/production/video_artifact.py`
  - 定义 reviewer protocol、exact evidence validation，并让 `VideoProbeReceipt` 可选绑定 commercial evidence。
- `src/ai_video/production/_lifecycle_schema.py`
  - 增加 commercial evaluation intent/evidence pointer/state 与 additive Manifest compatibility。
- `src/ai_video/production/_state_commit_video_candidate.py`
  - 在 candidate preparation 中调用 commercial checkpoint；PASS 前不形成 candidate。
- `src/ai_video/production/_state_commit_video_recovery.py`
  - 对 intent-only unknown outcome、evidenced result 和 explicit recovery 建立与 continuity 相同的 fail-closed规则。
- `src/ai_video/production/_video_project_reader.py`、`src/ai_video/production/paths.py`
  - 只负责 canonical reopen/path validation。
- `src/ai_video/production/video_generation.py`
  - `validate_once()` 与 legacy `fetch_and_activate()` 透传 optional commercial reviewer；两条 public path 必须同样 enforce，不能留下 bypass。
- `src/ai_video/production/models.py`
  - `QaPolicy` 增加 optional `domain_acceptance`；legacy policy 未设置时保持现有 generic semantics。
- `src/ai_video/production/review.py`
  - `SEMANTIC` adjudication 在 selected policy 含 domain acceptance 时委托 typed domain validator；不把 Ecommerce 规则直接堆进该大模块。
- `src/ai_video/production/__init__.py`
  - 只暴露批准的 public profile/result/coordinator types。

### Canonical modules not modified by default

- `src/ai_video/production/ad_creative.py`
- `src/ai_video/production/composition.py`
- `src/ai_video/production/hyperframes.py`

它们由 integration tests 验证。若发现真实 contract gap，先记录 failing test、缺失 binding 和最小 change surface，再单独修改；不得预先扩张这些模块。

## Contract Design

### DomainAcceptancePolicy

`DomainAcceptancePolicy` 是 `QaPolicy` 内的 optional nested sealed contract：

- `domain_id`: 本计划固定 `ecommerce`。
- `profile_id` / `profile_version` / `profile_content_hash`。
- `profile_payload`: deep-immutable canonical JSON snapshot；Ecommerce Gate 必须重新 `model_validate()` 为 `EcommerceAcceptanceProfile`，且其 canonical hash 必须等于 `profile_content_hash`。
- `measurement_contract_version`: 初始为 `ecommerce-media-acceptance/1`。
- `required_requirement_ids`: exact ordered unique IDs。
- `semantic_authorities`: 继续使用 `QaPolicy.semantic_authorities`，不得出现第二份 authority list。

Profile snapshot 内嵌于 selected `QaPolicy`，避免新增第二个 durable profile registry/pointer。`required_requirement_ids` 必须与 typed profile payload 的 required IDs exact 一致；first-appearance window、end-card duration、applicability 等参数也由该 snapshot 冻结，不能只绑定一个无法 reopen 的 hash。

当 `QaPolicy.semantic_requirement="required"` 且 `domain_acceptance` 存在时：

- P6 `SEMANTIC` evidence 必须匹配 domain/profile/measurement contract。
- requirement IDs 必须 exact coverage；少一个、多一个、重复或顺序漂移都为 `NOT_EVALUATED`。
- 任一 required `FAIL` 为 overall `FAIL`；任一 `NOT_EVALUATED` 为 overall `NOT_EVALUATED`。
- Authoring `ready`、`AdCreativeReviewReport` 或 free-form `semantic_match=true` 不能升级为 PASS。

Legacy `QaPolicy.domain_acceptance=None` 继续走现有 generic semantic behavior。

### GeneratedCommercialShotBinding

每个需要 post-media commercial review 的 `ResolvedVideoGenerationRequest` 绑定：

- `ad_creative_plan_id` 与 content hash。
- `commercial_execution_projection_hash` 与 `target_shot_id`。
- selected profile hash 与 applicable requirement IDs。
- Product Truth/product reference/source approval hashes；无产品要求的 performance Shot 保留空 product tuple。
- resolved generation hash、output asset ID 和 expected actor IDs。

Binding 是 request identity 的一部分。替换 plan、projection、source approval、profile 或 Shot requirement 必须改变 request hash并使旧 evidence 失效。

### GeneratedCommercialShotEvidence

Evidence 绑定 held MP4 bytes hash、measured metadata、request binding、evaluator identity/profile 与逐 requirement findings。初始 Shot requirements：

- `shot.identity.main_character`
- `shot.identity.elder`
- `shot.cast.allowed_count`
- `shot.product.presence_window`
- `shot.product.packaging_identity`
- `shot.product.label_fidelity`
- `shot.product.interaction`
- `shot.dialogue.verbatim`
- `shot.dialogue.speaker_binding`
- `shot.motion.required`
- `shot.camera.intent`
- `shot.continuity.in_out`

Applicability 来自 exact Shot projection/profile。例如只有 recommendation Shot 强制老人；只有 on-camera speech Shot 强制 lip-sync；product hero/end card 不要求 generated physical interaction。

Evaluator authority 至少为 `EXPLICIT_EVALUATOR` 或 `HUMAN`。包装小字、真实手部接触、人物 identity、说话人和 lip-sync 无可信 evidence 时必须为 `NOT_EVALUATED`。

### Whole-Ad Ecommerce Evidence

Whole-ad evidence 同时绑定：

- exact `AdCreativePlan`/profile hashes。
- ordered accepted Shot IDs、request hashes、generated bytes hashes 和 commercial evidence hashes。
- `CompositionSpec` hash、`ResolvedTimeline` fingerprint、HyperFrames render state/output hash。
- exact Gate 1 profile/context/policy identities。
- evaluator/human identity 与逐 requirement findings。

Whole-ad requirements：

- `ad.hook.first_second`
- `ad.arc.problem_recommendation_use_payoff`
- `ad.cast.elder_interaction`
- `ad.product.first_appearance`
- `ad.product.exposure_balance`
- `ad.product.packaging_consistency`
- `ad.audio.coverage`
- `ad.audio.product_recommendation`
- `ad.audio.voice_continuity`
- `ad.cta.brand_closure`
- `ad.continuity.character`
- `ad.motion.required_windows`
- `ad.edit.pacing`
- `ad.copy.claim_compliance`
- `ad.delivery.duration_aspect`

Gate 2 PASS 只说明 exact Ecommerce requirements 完整通过；它必须转换为 current P6 `SEMANTIC` ReviewEvidence/Receipt，仍不等于 Final Acceptance 或 human watchability approval。

## Qingyan Profile Rules

### Cast and narrative

- 苗家女孩为 20–25 岁主角，现代苗族元素，不限定全片只有一个人。
- 老人必须出现在 recommendation beat，与女孩发生可见的对视、递产品、示范、回应或共同推荐；背景路过不算。
- 实际成片广告弧必须可识别为：热/汗湿尴尬 -> 老人推荐 -> 女孩拿出/使用 -> 清爽自信 -> product hero + CTA。

### Product timing and packaging

- 产品首次清晰出现目标为 3–6 秒；不要求每个 Shot 手持。
- 人物手持/使用必须通过 generated-video temporal evidence，source image approval 不足以代替。
- 黄色盒体、黄色瓶身标签、白色瓶盖、瓶型与盒型必须跨所有产品出现保持一致。
- Hero/CTA 优先使用 registered readable packshot pixels；generated in-hand Shot 不能替代包装真值。
- Flat overlay、extra hands、穿模、错误比例或错误包装均阻断对应 requirement。

### Copy, audio and CTA

- 必须有老人推荐产品的可听台词，以及女孩承接卖点或 CTA 的可听台词。
- Exact copy 走 existing `AudioTrackSpec`、voice asset、CaptionTrack 和 canonical timeline；不依赖生成视频原生音频保证逐字正确。
- 非 intentional silence 不能用 `anullsrc` 伪造 coverage。
- On-camera speech 绑定 speaker、verbatim line、Shot timing 与 lip-sync evidence。
- Claim 只允许 Claim Ledger 内表达，例如“帮助减少汗湿困扰”“抑汗净味”“清爽舒适”；禁止医疗治疗和绝对时效承诺。

### Motion and static media

- `GENERATED_VIDEO`/`EXISTING_VIDEO` required-motion windows 复用 Technical layer 的 `frozen_required_motion`、frame diversity 与 window strategy。
- Ecommerce semantic evidence判断动作是否完成、互动是否真实、节奏是否服务广告弧；不使用一个 aggregate motion score 抵消失败。
- Failed required-motion Shot 不得以静帧、clone freeze、Ken Burns zoom 或无关 B-roll 静默替换。
- Explicit product hero/end card 可使用 deterministic motion graphics；end card duration 上限 2.0 秒，并必须在 plan/timeline 中显式存在。

## Major Milestones

### Milestone 1: Freeze typed policy and RED boundaries

**Files:**

- Create `src/ai_video/production/domain_acceptance.py`
- Create `src/ai_video/production/ecommerce_media_acceptance.py`
- Create `tests/test_production_ecommerce_media_acceptance.py`
- Modify `src/ai_video/production/models.py`
- Modify `tests/test_production_review.py`

**Contract:** 新 domain policy 是 `QaPolicy` 的 optional additive field；Ecommerce profile、requirements 和 findings sealed 且 exact coverage。Legacy policy behavior不变。

**RED cases:** missing/extra/reordered requirement、wrong profile hash、unauthorized evaluator、authoring-ready masquerading as semantic evidence、required `FAIL`/`NOT_EVALUATED`、render/timeline mismatch。

**Acceptance:** RED tests 精确失败在 typed domain seam 缺失；已有 generic P6 semantic tests 继续通过。

### Milestone 2: Gate generated Shot candidate before activation

**Files:**

- Modify `src/ai_video/production/video.py`
- Modify `src/ai_video/production/commercial_execution.py`
- Modify `src/ai_video/production/video_artifact.py`
- Create `src/ai_video/production/_state_commit_video_commercial.py`
- Modify `src/ai_video/production/_lifecycle_schema.py`
- Modify `src/ai_video/production/_state_commit_video_candidate.py`
- Modify `src/ai_video/production/_state_commit_video_recovery.py`
- Modify `src/ai_video/production/_video_project_reader.py`
- Modify `src/ai_video/production/paths.py`
- Modify `src/ai_video/production/video_generation.py`
- Create `tests/test_production_ecommerce_shot_candidate_gate.py`
- Modify `tests/test_production_generated_video_e2e.py`

**Contract:** commercial-bound request 在 `VALIDATE` phase 建立 durable intent，再调用 reviewer，再持久化 exact evidence。PASS 前不得进入 `CANDIDATE`/`ACTIVATE`；unknown outcome 必须 explicit recovery，不得 blind rerun。

**Compatibility:** additive Manifest schema target 为 `2.13`。Readers 继续接受旧 2.10–2.12 attempts；旧 attempt 没有 commercial binding 时不要求新 checkpoint；新 commercial binding 不得降级写回旧 schema。

**Acceptance:** held-FD bytes replacement、profile/request mismatch、reviewer异常、`FAIL`、`NOT_EVALUATED` 和 intent-only recovery 均 fail closed；`validate_once()` 与 legacy `fetch_and_activate()` 都无法绕过。

### Milestone 3: Enforce sequential Shot stop barrier

**Files:**

- Create `src/ai_video/production/ecommerce_ad_coordinator.py`
- Create `tests/test_production_ecommerce_ad_coordinator.py`
- Modify `tests/test_production_ecommerce_product_interaction_e2e.py`

**Contract:** coordinator 只调用 existing public services：start/submit/poll/fetch/validate/activate。它不读取 credential、不选择 Provider、不直接写 Manifest，也不批量预提交。

**Ordering:** Shot N 必须完成 exact commercial validation PASS 和 activation，才可创建/submit Shot N+1 attempt。`FAIL`、`NOT_EVALUATED`、stale、unknown outcome 或用户 STOP 后，later submit counter 必须保持 0。

**Acceptance:** effect-counter tests 覆盖 local/paid service facade、first/ middle/last Shot failure、resume 与 duplicate invocation；replay 不重复 Provider effect。

### Milestone 4: Run a one-Shot empirical checkpoint

**Authorization:** 该 milestone 是新的 live/paid execution gate。只有用户在执行时明确授权 exact Provider/model/input/budget/output 后才能运行；代码计划或 credential 存在不构成授权。

**Pilot:** 只生成一个“老人向苗家女孩递出并推荐青颜喷雾”的 product-interaction Shot。固定 product reference、人物 reference、prompt、seed/mode 和 evaluator profile，只检验 post-media Gate 是否能区分：老人互动、产品包装、hand-object contact、台词/说话人和 required motion。

**Acceptance:** evaluator 给出 requirement-level findings，人类 normal-speed review 复核。若 Gate PASS 但人类明显拒绝，先校准 requirement/evaluator，不继续构建 whole-ad Gate；若 Gate FAIL 正确阻断，才进入下一 milestone。

### Milestone 5: Implement Whole-Ad Ecommerce Gate 2 and P6 bridge

**Files:**

- Create `src/ai_video/production/ecommerce_quality_gate.py`
- Modify `src/ai_video/production/review.py`
- Modify `src/ai_video/production/_state_commit_review.py` only if exact typed-payload reopen cannot be enforced through existing `record_review_receipt()` contract
- Create `tests/test_production_ecommerce_quality_gate.py`
- Modify `tests/test_production_quality_gate_coordinator.py`
- Modify `tests/test_production_review.py`

**Contract:** Gate 2 只接受 `UniversalQaGateResult(verdict=PASS, eligible_for_domain_gate=true)` 且 exact context current。它纯计算 findings，并生成与 current `ReviewRequest` identity 一致的 `QaLayer.SEMANTIC` ReviewEvidence；P6 committer负责 durable request、one-use analysis permit、receipt和lifecycle。

**Exact ordering:** 先运行 Gate 1；再由 `begin_review()` 持久化只请求 `QaLayer.SEMANTIC` 的 current `ReviewRequest`；随后把 Gate 2 coordinator 作为 analyzer 传给 `run_review_analysis()`，让 one-use permit 包围实际 evaluator invocation；最后才调用 `record_review_receipt()`。不得在 durable request 之前预跑 Gate 2 后补写 receipt。

**Acceptance:** Gate 1 missing/failing/stale 时 Gate 2 evaluator call count 为 0；Gate 2 missing coverage不能生成 PASS receipt；profile swap、render replacement、timeline change、Shot evidence replacement均失效；Final Acceptance 必须重新打开 semantic receipt并验证 PASS/current。

### Milestone 6: Canonical composition/render integration without parallel final path

**Files:**

- Create `tests/test_production_ecommerce_post_media_e2e.py`
- Modify `src/ai_video/production/ecommerce_ad_coordinator.py`
- Modify `tests/test_production_ad_creative.py`
- Modify `tests/test_production_composition.py` and `tests/test_production_hyperframes.py` only for integration coverage

**Contract:** coordinator 只能使用 `CompiledAdCreativeHandoff.composition_spec`、accepted/activated Shot assets、`resolve_composition()` 和 HyperFrames public adapter。它不能 shell out 到 ad-hoc FFmpeg final script，也不能重算 duration/order/audio。

**Acceptance:** exact final candidate 可追溯 plan -> projection -> Shot request/evidence -> active assets -> composition -> timeline -> render -> Gate 1 -> Gate 2 -> P6 receipt。缺少任一 binding 的 manual MP4 只能标记 development experiment，不能进入 P6-ready。

### Milestone 7: Docs, policy, full verification and 25–30s pilot

**Files:**

- Modify `.agent/harness/policy.yaml`
- Modify `tests/test_agent_harness_policy.py` if routing changes
- Modify `docs/agent-primary-contract-matrix.md`
- Modify `docs/v0.2-runtime-baseline.md`
- Modify `docs/v0.2-agentic-production-roadmap.md`

**Contract:** 文档只记录 exact verified implementation；Shot Gate、Gate 1、Gate 2、P6 和 human Final Acceptance 的 owner/禁止旁路必须分开。

**Pilot:** 获得单独授权后，通过 canonical lifecycle 生成 25–30 秒、9:16、4–8 Shot 青颜 candidate。逐 Shot 顺序执行，不提前 batch submit；normal-speed 比较 positive、negative 和新 pilot。

**Acceptance:** 新 pilot 明显击败 negative artifact，并且相对 positive comparison 不退化叙事连贯性、老人互动、连续口播、包装可辨识度、真实动态和 CTA。人工 verdict 按 requirement 记录时间戳，不计算 aggregate score；人类 GO 前不得扩 batch或声称 Final。

## Required Test Matrix

| Scenario | Expected |
| --- | --- |
| Legacy non-commercial video request | Existing behavior unchanged |
| Commercial request without selected profile | Fail before reviewer/provider continuation |
| Candidate bytes replaced after held-FD measurement | Reject exact binding |
| Shot evidence missing one applicable requirement | `NOT_EVALUATED`; no activation |
| Product interaction uses flat overlay/extra hands | `FAIL`; no activation |
| Elder required but absent/background-only | `FAIL`; no next submit |
| Wrong speaker/verbatim line/lip-sync unevaluated | `FAIL` or `NOT_EVALUATED`; no next submit |
| Shot N PASS/current/activated | Shot N+1 eligible |
| Shot N unknown outcome | Explicit recovery required; later submit count 0 |
| Gate 1 not current PASS | Gate 2 evaluator count 0 |
| Gate 2 free-form semantic_match only | `NOT_EVALUATED` |
| Gate 2 exact requirement coverage PASS | Eligible for P6 semantic receipt |
| Render/timeline/profile/plan changed | Prior Gate 2 evidence stale |
| Manual FFmpeg MP4 without canonical bindings | Not P6-ready |
| All receipts PASS but no committer Final Acceptance | Candidate only |

## Verification Commands

Focused suite during implementation:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_ecommerce_media_acceptance.py \
  tests/test_production_ecommerce_shot_candidate_gate.py \
  tests/test_production_ecommerce_ad_coordinator.py \
  tests/test_production_ecommerce_quality_gate.py \
  tests/test_production_ecommerce_post_media_e2e.py \
  tests/test_production_ecommerce_product_interaction_e2e.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_quality_gate_coordinator.py \
  tests/test_production_review.py \
  tests/test_production_ad_creative.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_ecommerce_ad_workflow_skill.py -q
```

Control-plane checks:

```bash
python -m scripts.docs_contract_gate check
python -m scripts.architecture_gate check
python scripts/agent_harness.py policy-audit
```

Exact staged verification:

```bash
python scripts/agent_harness.py inspect --staged
python scripts/agent_harness.py verify --staged --run-id qingyan-ecommerce-post-media-gate
python scripts/agent_harness.py verify-receipt .agent/harness/runs/qingyan-ecommerce-post-media-gate/receipt.json
```

完成 task-owned commit 后，再按 `.agent/harness/policy.yaml` 对 exact commit range 运行 verify。Receipt、technical tests、Gate PASS 和人工观看结论必须分层报告，不能互相替代。

## Human Acceptance Checklist

- 0–3 秒自然表达热、汗湿或异味顾虑。
- 3–6 秒内产品首次清晰出现。
- 老人与苗家女孩有可见互动，且老人真正说出推荐话语。
- 女孩至少一次自然手持/使用产品，但不要求每个 Shot 都出现产品。
- 黄色盒体、黄色瓶身标签、白色瓶盖、瓶型盒型跨镜头一致。
- 全片存在可听、连贯、准确的产品推荐；不是只有 BGM/字幕。
- Claim 符合 ledger，无治疗、根治或绝对保证。
- 人物 face/服装/银饰/空间方向/光线连续。
- Required beats 真实动态，无隐藏静帧、长 freeze 或无意义 zoom。
- Product hero 与 CTA 同时可见、可听、清晰。
- 成片 25–30 秒、9:16，并以 normal speed 完整观看。

## Definition of Done

1. Exact commercial requirement binding 进入 generated video request identity。
2. Post-media Shot review 在 `validate_once()` candidate seam durable checkpoint，PASS 前不能 activation。
3. Shot N 未 PASS/current/activated 时，Shot N+1 Provider submit effect 为零。
4. Whole-ad Gate 2 必须消费 current Gate 1 PASS，并逐 requirement fail closed。
5. Gate 2 evidence 通过 existing P6 `SEMANTIC` ReviewEvidence/Receipt 持久化，不出现第二 evidence lifecycle。
6. Final candidate 只消费 accepted assets，并走 `CompositionSpec -> ResolvedTimeline -> HyperFrames`。
7. Existing committer、Provider lifecycle、timeline、renderer、P6/Final Acceptance ownership不变。
8. Focused/full tests、policy、exact-snapshot Harness 与 independent `reviewer_xhigh` 通过。
9. One-Shot empirical checkpoint 和 whole-ad pilot 均有 requirement-level human evidence；未验证项保持 `NOT_EVALUATED`。

## Recommended Commit Boundaries

1. `test: define typed ecommerce media acceptance policy`
2. `feat: checkpoint commercial generated-shot review`
3. `feat: stop ecommerce generation after failed shot`
4. `feat: bridge ecommerce gate two into p6 semantic review`
5. `test: prove canonical ecommerce post-media lifecycle`
6. `docs: record ecommerce post-media acceptance boundary`

每个 commit 只 stage task-owned files。实施前重新检查 current working tree 和 live writer ownership；same-file overlap 必须先由用户决定顺序，unrelated changes 必须保留。
