# Qingyan Ecommerce Post-Media Gate Repair Plan

> **Implementation mode:** 本文只定义修复边界、契约、任务顺序与验收方法；本轮不修改 Runtime、不提交 Provider 请求、不生成媒体。实施者应按 milestone 顺序执行，并在每个 milestone 完成 RED/GREEN verification 后再进入下一阶段。

## Goal

修复青颜广告链路中“前置 authoring Gate 很强，但最终视频反而更差”的结构性问题：让每个生成 Shot 在下一次 Provider submit 前接受真实媒体检查，让整片在 Universal QA 之后接受 Ecommerce 专属 Gate 2，并保证最终候选只能由 `AdCreativePlan -> CompositionSpec -> ResolvedTimeline -> HyperFrames` 的 canonical path 产生。

目标成片为 25–30 秒、9:16、动态视频优先的抖音信息流广告。苗家女孩是主角，但不是唯一人物；必须有老人和女孩的有效互动与推荐话语，产品在合适 Shot 中由人物持有或使用，并保持黄色盒体、黄色瓶身标签、白色瓶盖、瓶型与盒型的一致性。全片必须具备连贯广告弧、可听懂的产品推荐、明确 CTA、人物连续性和可验证的产品包装一致性。

## Problem Statement

当前失败不是“前置 Gate 不够多”，而是 Gate 与真实媒体之间存在三处断裂：

1. `AdCreativePlan`、authoring G0–G7 与 `AdCreativeReviewReport` 只能证明离线创意合同和 deterministic projection；它们不能证明生成后的 MP4 中真的有人物、老人、产品、动作、口播和包装一致性。
2. 当前逐镜头检查不是 Provider submit 之间的同步阻断条件。一个 Shot 失败后，后续生成仍可能继续；失败动态镜头还可能在后期被静帧、freeze、zoom 或无对白 BGM 替换，导致“技术上完成、观感上退化”。
3. 当前青颜 T8 成片通过手工 FFmpeg 脚本拼接，绕过 canonical `CompositionSpec -> ResolvedTimeline -> HyperFrames`、P6 与 Final Acceptance。该脚本丢弃原生音频、使用 `anullsrc`，并把大量静帧或 clone freeze 当作视频时长。

因此，修复的 single owner 不是 authoring Skill，而是 Production Runtime 中新的 Ecommerce post-media acceptance boundary。它只判断和编排，不获取第二套 timeline、不选择第二个 renderer、不写第二份 lifecycle state。

## Evidence Baselines

以下两个本地文件只用于本轮人工 A/B 与回归分析，不得成为单元测试、Runtime 配置或发布流程的硬编码依赖：

- Positive comparison baseline: `/home/reggie/电商图片/青颜/青颜视频_20260825_miaozu/青颜_苗家女孩与老人_30s连续口播广告_candidate.mp4`
- Negative regression artifact: `/home/reggie/vscode_folder/AI-VIDEO/artifacts/qingyan-miao-ad-20260825/final/青颜_苗家女孩T8动态广告_28s_9x16.mp4`

Positive baseline 不是自动 PASS 的 golden artifact。它只代表当前人类偏好的相对方向，仍需逐 requirement 评估包装、互动、claim 与连续性。Negative artifact 应稳定暴露至少以下失败：缺少老人互动、缺少连续产品推荐口播、产品使用镜头未进入成片、静帧或 freeze 比例过高、手工 render provenance 不完整。

## Scope

### In Scope

- Generated Shot video 的 post-media Ecommerce requirement evaluation。
- Provider submit 之间的同步 stop barrier。
- Whole-ad Ecommerce Gate 2，位于 Universal QA Gate 1 之后、P6/final acceptance 之前。
- Ecommerce acceptance profile、stable requirement IDs、exact evidence coverage 与 content-addressed binding。
- Canonical composition、audio/captions、timeline 与 HyperFrames render handoff。
- 青颜 profile 的人物、老人互动、产品出现时点、包装一致性、广告语、CTA、动态覆盖和人物连续性要求。
- Focused tests、Harness policy routing、canonical docs 和一个真实 25–30 秒 pilot 的人工 A/B。

### Out of Scope

- 新 Provider、新模型或 Provider selection path。
- 新 CLI、新 runtime dependency、新 Manifest writer 或自动 repair/retry。
- 自动激活 candidate、自动推进 P6、自动 Final Acceptance。
- 用一个 aggregate quality score 代替 requirement-level verdict。
- 把 `ecommerce-ad-workflow` G0–G7 扩成媒体验收系统。
- 把 external Skill、FFmpeg 拼接脚本或本地 artifact 目录变成 production truth。
- 本计划阶段的任何 paid/remote submit 或媒体生成。

## Ownership and Invariants

| Concern | Owner after repair | Invariant |
| --- | --- | --- |
| Creative/product/copy intent | `AdCreativePlan` + Ecommerce authoring package | Authoring readiness 不能冒充媒体质量通过 |
| Generated Shot acceptance | Ecommerce post-media evaluator | Pure、exact-input-bound、requirement-level |
| Gate ordering | Ecommerce quality coordinator | Gate 1 必须先 PASS/current，Gate 2 才可执行 |
| Submit sequencing | Ecommerce ad execution orchestrator | Shot N 未 PASS 前不得 submit Shot N+1 |
| Timing/order/frame/sample | `ResolvedTimeline` | 任何 Gate 或 execution helper 不得重算 timeline |
| Render | HyperFrames adapter | 不允许手工 FFmpeg 形成第二条 final path |
| Durable state/P6/activation/recovery | `ProductionStateCommitter` | 新模块不得直接写 Manifest 或 active pointer |
| Provider lifecycle | Existing Provider router/service | 不 blind retry、不 remint permit、不绕过 budget/egress/provenance |
| Final human quality judgment | Existing P6/Final Acceptance lifecycle | Domain Gate PASS 不等于人类 watchability PASS |

Unchanged public contracts：Legacy `0.1.x` CLI、Provider routing、Budget Guard、Cloud Egress、one-use permit、Registry、Dependency Graph、P4 audio/caption ownership、P6 lifecycle 与 HyperFrames default renderer 全部保持不变。

## Target Architecture

```text
AdCreativePlan + Product Truth + Claim Ledger
  -> compile_ad_creative_handoff
  -> sequential Shot execution
       -> existing Provider submit/fetch once
       -> bind exact generated MP4 bytes
       -> Shot post-media Ecommerce requirements
       -> PASS: next Shot is eligible
       -> FAIL / NOT_EVALUATED: stop, zero later submits
  -> accepted Shot set only
  -> CompositionSpec
  -> ResolvedTimeline
  -> HyperFrames candidate render
  -> Universal QA Gate 1
  -> Ecommerce Whole-Ad Gate 2
  -> eligible for existing P6 / ProductionStateCommitter
  -> human Final Acceptance
```

Gate 2 只消费 Gate 1 的 current PASS result；它不得调用 Provider、renderer、committer 或 repair。任意 input identity、profile hash、evidence hash、timeline fingerprint、render hash 不匹配时，结果必须 fail closed。

## Domain Contract

### 1. New pure post-media contract

Create `src/ai_video/production/ecommerce_media_acceptance.py`，承载以下 cohesive responsibilities：

- `EcommerceMediaRequirementScope`: `SHOT`、`WHOLE_AD`。
- `EcommerceMediaRequirement`: stable ID、scope、applicability、required evidence kinds、human/evaluator authority。
- `EcommerceMediaAcceptanceProfile`: versioned、content-addressed requirement set 与 profile parameters。
- `EcommerceMediaEvidence`: target bytes identity、tool/actor identity、measurement、source artifact identity 与 freshness metadata。
- `EcommerceMediaFinding`: `PASS`、`FAIL` 或 `NOT_EVALUATED`，并绑定 exact requirement ID 与 evidence IDs。
- `EcommerceMediaAcceptanceResult`: exact-input summary、all findings、blocking reasons、profile hash、target hash；不得只有一个 score。

Evaluator 必须是 pure function。任何 required requirement 为 `FAIL` 或 `NOT_EVALUATED`，或者 required evidence 缺失、重复、过期、target hash 不匹配时，整体不得 ready。

### 2. Reuse existing commercial visual evidence

保留 `src/ai_video/production/commercial_visual_review.py` 作为 source-image visual review owner。不要把 `CommercialSourceReviewReceipt(target_kind="source_image")` 伪装成 generated Shot 或 whole-ad 证据。

Generated Shot video 需要 temporal evidence，至少覆盖：

- 人物 identity 与允许 cast count。
- 产品是否在要求的时间窗出现。
- 黄色包装盒、黄色瓶身标签、白色瓶盖、瓶型与盒型的一致性。
- hand-object contact、遮挡、extra fingers/hands、flat overlay 与穿模。
- 口型/说话人/台词绑定。
- required motion、camera intent 与入出状态连续性。

包装小字、真实 contact 与人物语义互动在 evaluator 未校准或证据不足时必须是 `NOT_EVALUATED`，不能靠“画面里有黄色区域”自动 PASS。

### 3. Qingyan requirement profile

Shot-level stable IDs：

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

Whole-ad stable IDs：

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
- `ad.motion.dynamic_coverage`
- `ad.edit.pacing`
- `ad.copy.claim_compliance`
- `ad.delivery.duration_aspect`

Applicability 必须来自 profile 与 plan，不是所有 Shot 都必须出现老人、产品或对白。例如：老人只在 recommendation/interchange beat 中 required；产品必须在 3–6 秒内首次清晰出现，并在 recommendation/use/hero/CTA 中按计划重复出现，但不要求每个 Shot 手持。

### 4. Exact identity binding

Shot result 至少绑定：

- sealed `AdCreativePlan` hash。
- Product Truth/product reference bytes hash。
- target `shot_id`、Shot intent hash、Provider request provenance。
- generated video bytes hash、duration、dimensions、stream identity。
- selected acceptance profile hash。
- evidence item hashes与 evaluator/actor identity。

Whole-ad result 额外绑定：

- ordered accepted Shot IDs 与每个 generated bytes hash。
- `CompositionSpec` hash。
- `ResolvedTimeline` fingerprint。
- HyperFrames render request/output hash。
- exact final candidate MP4 hash。
- Gate 1 result identity 与 Gate 2 profile hash。

任何 plan re-seal、Shot reorder、media replacement、timeline change、render replacement 或 evidence reuse 导致 hash/fingerprint 不一致时，旧结果必须失效。

## Media Acceptance Rules

### Narrative and cast

- 苗家女孩是 20–25 岁现代苗族气质主角，跨 Shot identity、服装核心元素、发饰与妆容可追踪。
- 老人必须至少出现在一个完整 recommendation interaction beat 中，与女孩发生可见的对视、递产品、示范、回应或共同推荐动作；仅在背景路过不算互动。
- 广告弧必须可从实际成片识别为：天气热/汗湿尴尬 -> 老人或同伴推荐 -> 女孩拿出并使用产品 -> 清爽自信 payoff -> product hero + CTA。
- 计划外主要人物、人物突然替换、年龄/服装/面部 identity 漂移均阻断相关 requirement。

### Product truth and timing

- 产品首次清晰出现目标为 3–6 秒；开场 0–3 秒优先交代痛点。
- 人物手持或使用镜头必须由 generated-video temporal review 验证，source image PASS 不足以证明成片 PASS。
- Product hero/CTA 优先使用已注册、可读的真实 packshot pixels；生成式持有镜头不得替代真实包装 hero truth。
- 不能通过二维贴图覆盖人物手部来伪造手持，也不能用错误瓶型、错误主色、错误瓶盖或不可辨识标签计为产品出现。

### Audio, copy and CTA

- 精确广告文案使用现有 `AudioTrackSpec`/voice asset/caption contract 和 canonical P4 timeline；不要依赖 H3 原生音频承载必须逐字正确的销售台词。
- 非创意性静默不得用 `anullsrc` 填满。实际 audio coverage 必须覆盖 `[0, duration]`，音乐、对白与 SFX 的职责明确。
- 老人必须有一句自然的产品推荐或使用建议；女孩必须有 payoff 或 CTA 台词。仅字幕、仅 BGM、仅环境音不满足 `ad.audio.product_recommendation`。
- On-camera speech 必须绑定 exact speaker、verbatim line、Shot timing 与 lip-sync evidence；未评估 lip-sync 时为 `NOT_EVALUATED`。
- 文案只能使用 Claim Ledger 已批准表达，例如“帮助减少汗湿困扰”“抑汗净味”“清爽舒适”；不得生成治疗、根治、医学保证或超时效 claim。
- CTA 必须同时具备可听推荐、品牌/产品可见和清晰落版；只出现产品静物但无行动/记忆文案不算完整 CTA。

### Dynamic-video rules

- Required live-action Shot 失败后，不允许静默替换为静帧、clone freeze、Ken Burns zoom 或无关 B-roll 后继续宣称该 beat 已完成。
- `source_kind=STATIC_IMAGE` 只允许用于显式 product hero/end card motion treatment；不能计入 live-action motion coverage。
- 明确 end card 最长 2.0 秒，必须有可见的 entrance/hold/exit deterministic motion，不得是未经处理的 raw still。
- 除显式 end card 外，每个 live-action beat 必须有测得的主体或镜头运动。Profile 初始阈值：全片 unintended freeze 累计不得超过 0.5 秒，单段不得超过 0.25 秒；超过即 `FAIL`。
- Threshold 必须 versioned 在 profile 中，后续只能基于标注 pilot 校准；不得把 optical-flow 数值当作人物互动、广告连贯性或 watchability 的替代品。

## Implementation Milestones

### Milestone 1 — Freeze contracts and create RED tests

**Files**

- Create `tests/test_production_ecommerce_media_acceptance.py`
- Create `tests/test_production_ecommerce_quality_coordinator.py`
- Create `tests/test_production_ecommerce_ad_execution.py`
- Modify `tests/test_production_commercial_visual_review.py`
- Modify `tests/test_ecommerce_ad_workflow_skill.py`

**Steps**

1. 为 requirement profile、exact evidence coverage、hash mismatch、missing/stale evidence 写 RED tests。
2. 固定 authoring G0–G7、source-image review、Shot post-media review、Gate 1、Gate 2、P6 的边界测试。
3. 写 effect-counter tests，证明 Shot N 为 `FAIL` 或 `NOT_EVALUATED` 时 Shot N+1 submit count 保持为零。
4. 写 negative-artifact characteristics 的 deterministic fixtures：missing elder、no dialogue coverage、required product-use beat absent、excess freeze、manual render provenance missing。
5. 不把两个本地 MP4 复制进 test fixtures；fixture 只表达可复现的 typed evidence 与 identity mismatch。

**Milestone acceptance**

- 新 tests 因缺少 Runtime contracts 而失败，失败原因与预期 boundary 一致。
- 既有 authoring tests 继续证明 `AdQCReport.ready`/`AdCreativeReviewReport.is_ready` 不等于 media acceptance。

### Milestone 2 — Implement generated-Shot acceptance and synchronous barrier

**Files**

- Create `src/ai_video/production/ecommerce_media_acceptance.py`
- Create `src/ai_video/production/ecommerce_ad_execution.py`
- Modify `src/ai_video/production/__init__.py`
- Modify `tests/test_production_ecommerce_product_interaction_e2e.py`

**Steps**

1. 实现 immutable requirement/profile/evidence/finding/result models 与 sealing validation。
2. 实现 pure Shot evaluator：exact target binding、applicability、coverage、PASS/FAIL/NOT_EVALUATED 聚合。
3. 在 execution orchestrator 中注入 existing Provider submit/fetch owner 与 post-media evaluator；禁止直接读取 credential、选择 Provider 或写 Manifest。
4. 强制顺序为 `submit once -> fetch/validate bytes -> Shot Gate -> next submit`。不得先 batch submit 后补审。
5. 任何 missing/unknown/timeout/stale review outcome 都停止，保留 evidence，且不 retry、不 remint permit、不继续后续 Shot。
6. 只有 exact ordered accepted Shot set 可交给 composition compiler；failed、unreviewed 或被替换的 media 不能进入 handoff。

**Milestone acceptance**

- Effect-counter tests 证明 barrier 位于两个真实 submit seam 之间。
- 物理产品互动必须同时有 source truth 和 generated-video temporal evidence；flat overlay、extra hands、穿模或错误包装阻断。
- 任何 media bytes replacement 都使旧 Shot result 失效。

### Milestone 3 — Add Whole-Ad Ecommerce Gate 2

**Files**

- Create `src/ai_video/production/ecommerce_quality_coordinator.py`
- Modify `src/ai_video/production/quality_gate_coordinator.py` only to expose/consume stable Gate 1 identity if current public result lacks it
- Modify `src/ai_video/production/ad_creative_review.py` only if an explicit media-acceptance handoff field is required; keep `production_verdict=None`
- Modify `tests/test_production_quality_gate_coordinator.py`
- Modify `tests/test_production_review.py`

**Steps**

1. Gate 2 coordinator 接收 current Gate 1 PASS result、exact whole-ad context 与 evidence；Gate 1 缺失、失败、过期或 identity mismatch 时零副作用退出。
2. 对全部 required whole-ad IDs 逐项计算 verdict；任何 required `FAIL`/`NOT_EVALUATED` 阻断。
3. 输出只表示 `eligible_for_existing_p6`，不得写 `production_verdict=PASS`、不得激活 candidate。
4. 证明一个 project/candidate 只能绑定一个 preselected Ecommerce profile hash；运行中 profile swap 必须失败。
5. 证明 manual FFmpeg MP4 在缺少 exact `CompositionSpec`、`ResolvedTimeline` 与 HyperFrames render binding 时不能进入 Gate 2 ready state。

**Milestone acceptance**

- Gate 1 和 Gate 2 均为显式调用、pure assessment boundary。
- Gate 2 既不能修复媒体，也不能调用 Provider、renderer、committer。
- Missing coverage 不会被一个总分或其他维度 PASS 抵消。

### Milestone 4 — Restore canonical final composition path

**Files**

- Modify `src/ai_video/production/ad_creative.py`
- Modify `src/ai_video/production/composition.py`
- Modify `src/ai_video/production/hyperframes.py`
- Modify `tests/test_production_ad_creative.py`
- Modify `tests/test_production_composition.py`
- Modify `tests/test_production_hyperframes.py`
- Modify `tests/test_production_ecommerce_ad_execution.py`
- Retire or demote `/home/reggie/vscode_folder/AI-VIDEO/artifacts/qingyan-miao-ad-20260825/compose_t8_dynamic.sh` as a non-production experiment artifact; do not edit generated artifacts unless separately authorized

**Steps**

1. 让 execution orchestrator 只从 accepted Shot handoff 构建 `CompositionSpec`；保留现有 compiler ownership，不在 orchestrator 复制 composition logic。
2. 由 `ResolvedTimeline` 唯一决定 Shot order、trim、duration、frame/sample boundaries、audio/caption timing。
3. 由 HyperFrames 输出 candidate，并绑定 exact render bytes；FFmpeg 仅作为 approved adapter 内的 technical primitive，不再作为 parallel final composition owner。
4. 把对白、旁白、音乐、SFX 与 captions 放入 canonical audio/timeline contract；禁止 `anullsrc` 伪造完整广告音轨。
5. 对 required motion Shot 禁止隐式 still/freeze fallback。需要 end card 时以 explicit motion-graphics directive 表达，并受 2.0 秒与 dynamic treatment 规则约束。
6. Render 后先 Gate 1，再 Gate 2；只有两者均 current PASS 才可交给 existing P6 lifecycle。

**Milestone acceptance**

- Final candidate provenance 可以从 MP4 bytes 反查 exact plan、accepted Shot set、composition、timeline、render 与两层 Gate result。
- 绕过 canonical path 的 MP4 最多是 development experiment，不得被标记为 P6-ready 或 Final。
- Failed dynamic Shot 不会被静帧拼接掩盖为完成。

### Milestone 5 — Policy, docs, full verification and empirical pilot

**Files**

- Modify `.agent/harness/policy.yaml`
- Modify `docs/agent-primary-contract-matrix.md`
- Modify `docs/v0.2-runtime-baseline.md`
- Modify `docs/v0.2-agentic-production-roadmap.md`
- Modify `tests/test_agent_harness_policy.py` if routing expectations require updates

**Steps**

1. 将新 production files 和 tests 映射到 existing commercial/review/composition/audio mandatory checks；unmapped path 必须继续 fail safe。
2. Contract matrix 明确：source-image review、Shot post-media Gate、Universal Gate 1、Ecommerce Gate 2、P6/Final Acceptance 各自 owner 与 forbidden bypass。
3. Runtime baseline 只记录已由 exact staged/commit-range receipt 证明的行为；不要把 pilot 或人工偏好写成 Runtime deterministic truth。
4. Roadmap 标记 Gate 2 的真实 implementation state，并保留未完成的 evaluator calibration、human acceptance 和 Provider empirical uncertainty。
5. 通过 existing lifecycle 生成一个 25–30 秒、9:16、4–8 Shot 的真实青颜 pilot；一次只提交当前 eligible Shot，不并行扩大 batch。
6. 以 normal-speed 完整观看比较 positive baseline、negative artifact 与新 pilot。每项 requirement 给出 PASS/FAIL/NOT_EVALUATED 和时间戳证据，不计算一个总分。
7. 只有新 pilot 明显击败 negative artifact，且相较 positive baseline 不退化叙事连贯性、老人互动、连续口播、包装可辨识度、动态感与 CTA，才由人类给出继续扩 batch 的 GO。

**Milestone acceptance**

- Code、tests、policy、canonical docs 与 receipt 对同一个 exact implementation snapshot 一致。
- Pilot 保持 candidate 身份，直到 P6 和 human Final Acceptance 真正完成。
- 未评估的 packaging small text、identity、lip-sync 或 watchability 明确保留为 `NOT_EVALUATED`，不被自动推断。

## Required Test Matrix

| Scenario | Expected result |
| --- | --- |
| Shot N Gate PASS/current | Shot N+1 submit eligible |
| Shot N FAIL | Stop; later submit count = 0 |
| Shot N NOT_EVALUATED/timeout | Stop; later submit count = 0 |
| Source image PASS but generated hand contact missing | Shot product interaction FAIL |
| Generated media bytes replaced after review | Prior result stale/invalid |
| Elder required but absent or background-only | `ad.cast.elder_interaction` FAIL |
| Dialogue/captions exist but audio is silent | Audio coverage/recommendation FAIL |
| Audio line exists but wrong speaker or timing | Speaker/verbatim requirement FAIL |
| Product appears after 6s with no approved exception | First-appearance FAIL |
| Yellow object with wrong bottle/cap/box identity | Packaging requirement FAIL |
| Required dynamic beat replaced by freeze/static | Motion requirement FAIL |
| Explicit 2s animated end card | Eligible if all other evidence PASS |
| Gate 1 missing/failing/stale | Gate 2 not executed; zero side effects |
| Whole-ad evidence misses one required ID | Gate 2 not ready |
| Profile hash swapped during execution | Fail closed |
| Manual FFmpeg MP4 lacks canonical bindings | Not eligible for Gate 2/P6 |
| All Gates PASS but no human Final Acceptance | Candidate only, never Final |

## Focused Verification

Run after each relevant milestone:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_ecommerce_media_acceptance.py \
  tests/test_production_ecommerce_quality_coordinator.py \
  tests/test_production_ecommerce_ad_execution.py \
  tests/test_production_commercial_visual_review.py \
  tests/test_production_ecommerce_product_interaction_e2e.py \
  tests/test_production_ad_creative.py \
  tests/test_production_quality_gate_coordinator.py \
  tests/test_production_review.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_ecommerce_ad_workflow_skill.py -q
```

Run canonical control-plane checks before completion:

```bash
python -m scripts.docs_contract_gate check
python -m scripts.architecture_gate check
python scripts/agent_harness.py policy-audit
```

Run Harness against the exact staged snapshot, then verify the emitted receipt:

```bash
python scripts/agent_harness.py inspect --staged
python scripts/agent_harness.py verify --staged --run-id qingyan-ecommerce-post-media-gate
python scripts/agent_harness.py verify-receipt .agent/harness/runs/qingyan-ecommerce-post-media-gate/receipt.json
```

After committing only task-owned files, run the corresponding exact commit-range verification required by `.agent/harness/policy.yaml`. Do not use unrelated dirty changes as test inputs or proof.

## Human Acceptance Checklist

Human review must watch the complete candidate at normal speed and record timestamps for every finding:

- 0–3s clearly communicates heat/sweat/odor embarrassment without vulgar framing.
- Product first appears clearly within 3–6s.
- An elder and the Miao girl visibly interact; the elder recommends or introduces the product.
- The girl visibly holds or uses the product in at least one approved Shot; the product need not appear in every Shot.
- Yellow box, yellow bottle label, white cap, bottle and box geometry remain recognizable across all product appearances.
- Spoken copy actually recommends the product; audio is continuous and intelligible.
- Claim wording stays within Claim Ledger and avoids medical/absolute promises.
- Character identity, wardrobe logic, direction of movement and lighting remain coherent.
- Required beats are genuinely dynamic; no disguised photo inserts, long freeze or meaningless zoom.
- Product hero and CTA are legible, audible and commercially clear.
- Total duration is 25–30 seconds and delivery aspect ratio is 9:16.
- New pilot is more coherent and commercially persuasive than the negative artifact and does not regress from the positive baseline on the user-prioritized dimensions.

## Definition of Done

The repair is complete only when all of the following are true:

1. Generated Shot review is a synchronous barrier before the next Provider side effect.
2. Whole-ad Ecommerce Gate 2 runs only after current Universal Gate 1 PASS and evaluates every required domain requirement separately.
3. Exact plan/product/Shot/composition/timeline/render/media/profile/evidence identities are bound and stale evidence fails closed.
4. Final candidates use only accepted Shot media and canonical `CompositionSpec -> ResolvedTimeline -> HyperFrames` execution.
5. Manual FFmpeg artifacts, source-image receipts, authoring readiness and technical Gate PASS cannot be promoted as whole-ad quality acceptance.
6. Existing `ProductionStateCommitter`, Provider lifecycle, P6 and human Final Acceptance ownership remain unchanged.
7. Focused tests、policy checks、exact-snapshot Harness receipt 与 independent review 全部通过。
8. 一个真实 25–30 秒 pilot 通过 requirement-level human A/B；未验证能力明确标记，不由 tests 或 Gate 自动代替。

## Implementation Order and Commit Boundaries

建议按以下 commit 边界实施，确保每一步可独立回滚和 review：

1. `test: define ecommerce post-media acceptance failures`
2. `feat: gate generated ecommerce shots before next submit`
3. `feat: add whole-ad ecommerce acceptance gate`
4. `refactor: route ecommerce candidates through canonical composition`
5. `docs: record ecommerce post-media gate contracts and evidence`

每个 commit 只 stage task-owned paths。若实施时发现任一 target file 已由其他 writer 修改，先停止并重新确认 same-file ownership；不得 reset、覆盖或把 unrelated changes 带入 commit。
