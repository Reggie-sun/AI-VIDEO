# AI-VIDEO Empirical Quality Reuse Validation Implementation Plan

## Status

Proposed。本 Plan 是
`docs/superpowers/specs/2026-08-27-ai-video-empirical-quality-evolution-and-commercial-qa.md`
的第一个 execution slice，只覆盖当前最需要验证的 empirical quality loop：关闭 Qingyan v10 的
whole-video human verdict，并用五条全新 30s 视频验证 Drama 与 Ecommerce 的可复用性。

本 Plan 不授权代码修改、Gate/schema/Console 扩张、Provider 或 paid submit、媒体生成、自动 repair、
candidate activation、P6 / Final Acceptance、训练、commit、push 或 release。每次真实 Provider/media
动作仍必须获得当次 exact scope 的独立授权，并继续通过既有 safety、budget、egress、permit 与 per-Shot
post-media Gate。

## Goal

验证以下核心假设：

> AI-VIDEO 当前已经具备把一部分 Drama 和 Ecommerce brief 做成用户愿意原样使用的 30s 视频的能力；
> 该能力能够跨内容、跨结构和跨产品复用，并且大多数 PASS 不依赖无限版本链或整片重建。

本阶段的成功标准不是增加 Gate 数量，也不是让 evaluator 报告更多 `PASS`，而是得到 exact artifact-bound、
uninterrupted `1.0x` whole-video human verdict。

## Why This Is The Immediate Slice

当前 Runtime 已具备：

- pre-submit `ShotReadinessGate` structural readiness；
- sequential per-Shot post-media stop barrier；
- Universal Gate 1 ordering；
- typed Ecommerce Gate 2 envelope；
- existing P6 Review / Repair 与 Final Acceptance lifecycle；
- content-addressed audio、timeline、render、candidate 与 evidence contracts。

当前缺口不是第三个 Gate，而是：

- Qingyan v4-v9 多次 technical/targeted PASS 后仍被 human FAIL；
- v10 exact 30s candidate 仍缺 uninterrupted whole-video final verdict；
- Drama 只有 E0-G 一条 development HUMAN PASS，尚未证明可复用；
- full-video human findings 仍分散在 records、run summaries 与对话中；
- current Q0 human binding主要服务 Shot continuity，不适合直接冒充whole-video acceptance；
- current Ecommerce evaluator是injected contract，尚无可信Production measurement implementation。

如果现在直接把 Claim Grounding、CTA Presence 和 Audio Loudness 升级成 hard Gate，会先要求新的
claim-ledger Runtime bridge、final-program loudness measurement policy 和 mixed-evidence contract。这属于新的
Gate engineering，不能替代当前最缺的真实复用证据。

因此本 Plan 直接执行：

```text
exact video
  -> technical/structural evidence
  -> uninterrupted 1.0x human verdict
  -> exact blocking findings
  -> at most one bounded repair
  -> new whole-video verdict
  -> cross-video failure comparison
```

## Scope

### In Scope

- 关闭 exact Qingyan v10 的 `HUMAN_PASS` / `HUMAN_FAIL`；
- 规划并完成五条全新的 30s validation videos：3 Drama + 2 Ecommerce；
- 每条视频执行完整播放、human verdict、failure span 与 repair outcome capture；
- 使用现有 Gate 维护 structural correctness，不扩张其职责；
- 用provisional taxonomy比较跨视频重复failure classes；
- 记录Commercial QA六项的human/deterministic/shadow evidence；
- 仅在满足明确trigger时运行bounded Seedance capability experiment；
- 在五条视频完成后决定继续empirical loop、进入evaluator shadow，或收缩回generation workflow。

### Out Of Scope

- 新 Gate、Gate 3、新 `QaLayer` 或第二 P6 lifecycle；
- `ShotReadinessGate` post-media扩张；
- 新 Q0 schema、dataset writer、Console、API server或queue；
- Product Fidelity、Usage Correctness或Hook Density automatic hard Gate；
- evaluator训练、微调、自动Provider selection或自动repair；
- selective rebuild或batch production implementation；
- 把development evidence升级为Production、P6、Final Acceptance或release truth；
- 本Plan编写任务中的任何Provider/media/runtime side effect。

## Frozen Ownership And Invariants

| Concern | Owner during this Plan | Frozen boundary |
| --- | --- | --- |
| Pre-submit eligibility | `ShotReadinessGate` | 只判断binding、eligibility与required assets |
| Per-Shot sequential barrier | Existing Agent-side post-media Gate | required `FAIL` / `NOT_EVALUATED`立即停止下一submit |
| Universal structural correctness | Existing Runtime validators + Gate 1 | 不增加subjective quality rule |
| Ecommerce acceptance envelope | Existing Ecommerce Gate 2 | 不创建新lifecycle；无可信evidence不得PASS |
| Drama subjective acceptance | Exact human verdict | 不复用Ecommerce rubric或伪造typed Drama Gate |
| Durable Production state | `ProductionStateCommitter` | 唯一writer；records不得推进state |
| Timeline/order/frame/sample | `ResolvedTimeline` | 不建立实验旁路timeline |
| Advisory empirical history | `docs/record_for_agent/` + eligible `runs/*/SUMMARY.md` | 不成为Manifest/P6 truth |
| Whole-video personal acceptance | User uninterrupted `1.0x` verdict | technical score与MCP success不能替代 |

任何human PASS都只绑定exact bytes。修复、重编码、音频替换、字幕调整或重新compose后必须生成新的SHA和新的
whole-video verdict。

## Resource Allocation

在本 Plan 完成前，planned effort固定为：

| Work | Allocation |
| --- | ---: |
| 真实generation、composition、完整观看与bounded repair | 55% |
| generation workflow、continuity与Provider单变量实验 | 20% |
| exact human failure evidence与provisional taxonomy | 15% |
| evaluator shadow observations | 10% |
| Gate、Q0 schema、Console与policy扩张 | 0% planned |

Gate出现阻断真实实验的deterministic regression时可以interrupt修复，但不得因此建立新的长期infrastructure
stream。

## Validation Portfolio

### Phase 0 Candidate

- Qingyan v10 exact final：
  `artifacts/qingyan-miao-ad-20260826-v10/final/青颜_苗家腋下止汗完整广告_30s_9x16_v10.mp4`
- Expected SHA-256：
  `44e153f748189acffc15951bcf842eea11d2a6a4f00efacd8af1e61ab824b455`
- Current boundary：technical `PASS_FOR_HUMAN_REVIEW`，`HUMAN_FINAL_ACCEPTANCE_PENDING`。

v10只用于关闭当前版本链，不计入后续五条new-video validation set。

### Phase 1 New Videos

| Slot | Domain | Required difference | Primary hypothesis |
| --- | --- | --- | --- |
| D1 | Drama | 新人物关系与新场景 | E0-G能力不依赖原角色或场景 |
| D2 | Drama | dialogue/performance-heavy结构 | continuity PASS可与可接受表演同时成立 |
| D3 | Drama | 明确动作或空间变化 | 非single-static setup仍可达到whole-video PASS |
| E1 | Ecommerce | 新SKU，非Qingyan spray mechanics | product truth与commercial arc能迁移 |
| E2 | Ecommerce | 不同creative structure或presentation mode | 成功不依赖Qingyan同一repair recipe |

同一brief的v2、v3、replacement Shot、不同seed或不同render不得计为新的validation video。

## Evidence Unit

每个validation candidate必须有一个human-readable evidence entry，放入当次既有run summary或
`docs/record_for_agent/` record。不得为本阶段再创建新Runtime schema或第二writer。

最小字段：

| Field | Requirement |
| --- | --- |
| Candidate ID | domain + brief + version，稳定且唯一 |
| Artifact | repository-relative或明确local path |
| SHA-256 | exact final bytes |
| Media identity | duration、fps、resolution、aspect、audio presence |
| Playback | target device/environment、`1.0x`、normal volume |
| Completion | 是否uninterrupted完整观看与试听 |
| Verdict | exact `HUMAN_PASS`或`HUMAN_FAIL` |
| Blocking findings | 最多三个；每个含time span与observable symptom |
| Accepted concerns | 用户明确接受但不阻断的问题 |
| Evidence boundary | development / candidate / P6 / Final Acceptance分别陈述 |
| Intervention | changed variable、held constants、expected closed failure |
| Outcome | repair后exact SHA与新verdict，或停止原因 |

不得只写“效果不好”“感觉不对”或aggregate score。每个blocking finding必须能够指向可观察span、动作、声音、
画面或因果结果。

## Provisional Failure Taxonomy

taxonomy在本Plan中是可演进label set，不是frozen policy。首轮允许使用：

- `technical.identity_or_decode`
- `technical.freeze_or_duplicate`
- `continuity.character`
- `continuity.camera_motion_tail`
- `continuity.direction_or_space`
- `performance.intent_not_readable`
- `narrative.causality_or_payoff`
- `product.fidelity`
- `product.usage_correctness`
- `product.before_after_not_established`
- `audio.dialogue_or_voice_coverage`
- `audio.naturalness_or_lipsync`
- `commercial.claim_grounding`
- `commercial.cta_presence_or_readability`
- `edit.pacing_or_visual_hierarchy`
- `other.provisional`

新增label必须保留observable symptom，不得因taxonomy缺项丢弃真实failure。只有同一failure class在至少两个
不同视频中重复，才成为Phase 2 evaluator benchmark候选。

## Milestone 0: Close Qingyan v10 Human Verdict

### Hypothesis

v10已关闭v4-v9主要blocking findings，用户愿意原样使用exact v10。

### Execution

1. 重新验证exact path与SHA；不允许用preview、intermediate Shot或旧version替代。
2. 在目标设备、正常音量、`1.0x`下uninterrupted完整观看和试听。
3. 给出`HUMAN_PASS`或`HUMAN_FAIL`，并按Evidence Unit记录。
4. `HUMAN_PASS`时冻结该exact artifact，不继续润色。
5. `HUMAN_FAIL`时先分类failure surface，不立即生成新variant。

### Continue

- `HUMAN_PASS`：进入Milestone 1；
- `HUMAN_FAIL`且blocking failure局限于不超过两个Shot或一个deterministic audio/composition surface：允许
  一次bounded repair，之后重新完整观看并产生新verdict。

### Stop Or Shrink

- failure需要重写whole-ad causality、product mechanism或多数Shots；
- 一次repair后又出现新的unrelated critical failure；
- verdict未绑定exact SHA或不是完整`1.0x`观看。

Stop后保留v4-v10为failure evidence，不继续v11/v12无限版本链。v10无论PASS/FAIL都不阻止使用new brief
验证知识迁移。

## Milestone 1: Freeze Five Brief-Level Experiments

### Hypothesis

五个slot能够隔离不同复用风险，而不是把同一创意改名后重复测试。

### Execution

对D1-D3、E1-E2分别冻结：

- brief与domain；
- duration、aspect、delivery target；
- character/product truth与approved references；
- Shot intent、required motion、dialogue/audio与CTA/claim requirements；
- preferred Provider/model/profile与fallback prohibition；
- human blocking rubric；
- maximum one localized repair；
- expected output destination与预算边界。

该冻结只形成experiment input，不授权live submit。缺exact Provider/model/capability、input identity、budget、
egress或permit时，状态为`BLOCKED_BEFORE_SUBMIT`，不得猜测或fallback。

### Continue

- 五个brief在人物、场景、结构或SKU上具有真实差异；
- 每个brief的blocking requirements可以在生成前清楚说明；
- 每个experiment能说明它验证哪一个复用假设。

### Stop Or Shrink

- slot只是同一视频的seed/版本变化；
- 同时改变过多Provider、prompt、composition与rubric变量，无法归因；
- required capability没有明确可执行path。

## Milestone 2: Execute One Candidate Cycle At A Time

### Hypothesis

现有structural Gates足以安全支撑真实实验；新增质量schema不是获得下一条PASS的前置条件。

### Per-Video Sequence

1. 完成domain authoring与sealed requirements。
2. 运行`ShotReadinessGate`；`BLOCKED`时回到authoring，不提交Provider。
3. 只使用已明确授权的Provider/model/profile和exact inputs。
4. 每个Shot exact MP4落盘后，按repository per-Shot post-media Gate同步分析。
5. required `FAIL` / `NOT_EVALUATED` / stale / identity mismatch时立即停止下一Shot。
6. 只有accepted Shots进入canonical composition与`ResolvedTimeline`。
7. 运行existing technical/structural checks；Ecommerce只有在exact typed evidence真实存在时才进入existing Gate 2。
8. 生成final exact SHA后，执行uninterrupted `1.0x` whole-video human review。
9. PASS则冻结；FAIL只允许一次满足repair条件的bounded intervention。

### Drama Boundary

Drama当前没有formal typed Gate 2 application caller。本Plan不得为了让流程看起来完整而复用Ecommerce
profile、generic `semantic_match`或fixture PASS。Drama以existing structural/continuity evidence加exact
whole-video human verdict判断development success，并明确标注不是P6/Final Acceptance。

### Ecommerce Boundary

Ecommerce authoring、Gate 1、Gate 2和P6 lifecycle保持分离。Authoring ready、technical PASS、Gate 2 profile
ID存在或evaluator `issues: []`都不能替代whole-video human verdict。

## Milestone 3: Commercial QA Evidence During Real Videos

### Hypothesis

Commercial QA六项能够从真实E1/E2 evidence中分出stable deterministic rules与human-first rules，而无需现在
扩大Gate。

### Capture Matrix

| Requirement | During this Plan | Hard Gate authority |
| --- | --- | --- |
| Hook Density | shadow observation；记录首秒cue与human hook verdict | none |
| Product Fidelity | human blocking finding；绑定exact source与output span | human only |
| Usage Correctness | human blocking；绑定SKU-specific usage truth | human only |
| Claim Grounding |记录deterministic graphic/copy lineage；generated speech不确定时标`NOT_EVALUATED` | existing authoring correctness only |
| Audio Loudness |记录exact final-program measurement；没有selected profile不判threshold PASS | existing structural audio only |
| CTA Presence |记录timeline presence、actual rendered visibility与human readability | existing authoring/timeline correctness only |

本阶段不得：

- 用source asset正确推导generated Product Fidelity PASS；
- 用模型常识推导Usage Correctness；
- 用“没有检测到claim”推导Claim Grounding PASS；
- 从单个v10的LUFS反推universal loudness threshold；
- 用CTA存在推导persuasiveness；
- 用Hook cue数量推导creative success。

### Continue

- E1/E2至少产生可比较的requirement-level human findings；
- 某项deterministic evidence能绑定exact timeline/render/audio bytes；
- 同一failure在不同video中重复，且observable rule稳定。

### Stop Or Shrink

- evidence只来自单一Qingyan版本；
- rule需要主观总分或经常被human推翻；
- 实现rule需要先增加大规模schema/lifecycle，而没有真实重复failure支持。

## Milestone 4: Seedance Decision Point

Seedance不是默认Provider或automatic fallback。只有满足以下任一trigger才进入一次bounded experiment：

1. 同一sealed Shot已在H3/T8完成两个受控attempt，并重复出现同一model-capability-limited failure；
2. synthetic/illustrated lane需要exact terminal-frame continuation，用于复核既有positive continuity evidence；
3. Seedance官方exact capability提供当前stack缺失的input/reference/motion carrier，且request contract可完整满足。

实验必须same intent、same input identity、same duration、same rubric，只改变Provider/model/profile一个变量。
一次submit后不blind retry、不追加variant、不自动fallback。

### Continue

- selected requirement相对H3/T8 baseline明确改善；
- 没有新增critical identity、camera、product或usage failure；
- exact artifact通过per-Shot Gate并获得human comparison verdict。

### Stop

- capability不支持required inputs；
- evidence identity不完整或outcome unknown；
- 需要多变量变化才能解释结果；
- first-frame-only I2V再次产生identity、camera velocity或motion-tail regression。

## Milestone 5: Cross-Video Decision

### Primary Continue Threshold

五条new videos中：

- 至少3条whole-video `HUMAN_PASS`；
- 至少包含2条Drama PASS与1条Ecommerce PASS；
- 大多数PASS不超过一次localized repair；
- 每条均有exact SHA与完整human evidence；
- PASS不依赖同一seed、同一场景、同一SKU或同一Provider-only trick。

达到阈值后进入下一独立slice：structured failure corpus + evaluator shadow benchmark。该下一slice才评估
Claim Grounding、CTA和program loudness的可信evidence producer，仍不自动获得hard Gate promotion。

### Stop Or Shrink Threshold

出现任一情况即停止Gate/evaluator扩张：

- 少于3条PASS；
- 只有E0-G相似setup可以PASS；
- 每条PASS都依赖whole-video rebuild或多轮不可归因repair；
- generation/provider variance使结果不可复现；
- failure taxonomy每条视频都完全重写，没有跨视频重复类。

收缩方向固定为generation workflow、continuity、authoring与Provider predictability，不转去继续堆Gate。

## Deliverables

本 Plan 执行完成时只要求以下deliverables：

1. v10 exact whole-video human verdict record；
2. D1-D3、E1-E2五个sealed experiment briefs；
3. 每条candidate的exact artifact identity、technical boundary与human verdict；
4. 每次bounded repair的changed variable、held constants与新verdict；
5. provisional cross-video failure matrix；
6. Commercial QA六项的observed evidence matrix；
7. Seedance experiments的trigger、baseline、single variable与stop/continue verdict（如实际触发）；
8. 最终`continue`或`stop/shrink`decision。

不要求Production Console、自动dataset ingestion、evaluator model、new Gate policy或batch runner。

## Acceptance Criteria

本 Plan 只有在以下条件全部满足时才视为完成：

1. v10得到exact SHA-bound uninterrupted `1.0x` human verdict。
2. 五条new videos均为不同brief，不用版本或seed凑数。
3. 每条有完整Evidence Unit；missing evidence不能被写成PASS。
4. 所有Agent-controlled multi-Shot generation遵守per-Shot synchronous stop barrier。
5. Drama与Ecommerce保持独立acceptance边界。
6. 每条FAIL最多执行一次符合条件的bounded repair。
7. Product Fidelity、Usage Correctness和Hook Density未被提前自动hard-block。
8. Claim、CTA和loudness只按真实evidence authority报告，没有过度外推。
9. Seedance只在明确trigger下使用，且保持single-variable comparison。
10. 最终按预先声明的3/5、2 Drama + 1 Ecommerce threshold作继续或收缩决定。

## Verification Contract

### This Plan Document

```bash
PYTHONDONTWRITEBYTECODE=1 python -m scripts.docs_contract_gate check
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness policy-audit
git diff --check -- docs/superpowers/plans/2026-08-27-ai-video-empirical-quality-reuse-validation.md
```

### Future Experiment Evidence

每个真实candidate至少验证：

- exact `sha256sum`；
- full decode、duration、fps、resolution、aspect与audio presence；
- required per-Shot project-local `video-analysis` MCP evidence；
- applicable existing Runtime/Harness checks；
- uninterrupted `1.0x` human verdict；
- repair前后各自独立artifact identity。

命令成功、MCP transport成功、technical score、Gate receipt或`issues: []`均不得替代human acceptance。

## Evidence Anchors

- `docs/superpowers/specs/2026-08-27-ai-video-empirical-quality-evolution-and-commercial-qa.md`
- `docs/superpowers/specs/2026-08-25-ai-video-quality-gate-architecture-separation.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/agent-primary-contract-matrix.md`
- `src/ai_video/production/quality_gate_coordinator.py`
- `src/ai_video/production/ecommerce_media_acceptance.py`
- `src/ai_video/production/ecommerce_quality_gate.py`
- `src/ai_video/production/ecommerce_ad_coordinator.py`
- `src/ai_video/quality_intelligence/models.py`
- `src/ai_video/quality_intelligence/_capture_human.py`
- `docs/record_for_agent/2026-08-24-shot-continuity-e0e-seed320005-replication.md`
- `docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md`
- `docs/record_for_agent/2026-08-22-t8-h3-seedance-mixed-shot-continuity-handoff.md`
- `docs/record_for_agent/2026-08-26-qingyan-v5-dialogue-seam-continuity-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v6-product-exposure-seam-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v7-final-two-shot-hard-cut-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v8-underarm-elder-dialogue-continuity-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v9-before-after-and-later-voice-repair.md`
- `docs/record_for_agent/2026-08-26-qingyan-v10-cap-mechanics-and-moving-comparison-blocker.md`

## Explicit Authorization Boundary

执行本 Plan 文件本身不等于授权后续任何Provider、media、Runtime mutation、P6、Final Acceptance、repair、
commit、push或release。后续执行必须按每个milestone的真实scope单独核对authorization和current runtime
evidence。
