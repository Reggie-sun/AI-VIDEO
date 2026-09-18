# AI-VIDEO Ecommerce Production Job Specification

## Status

Proposed design specification。本文定义从现有 `ecommerce-ad-workflow/package/2` 到 exact Final Acceptance 与 delivery bundle 的 application-layer contract；它不是 current runtime capability 声明，也不授权 Provider submit、媒体生成、Production mutation、schema migration、public CLI change 或 release。

本文继承并收敛以下已实现边界：

- `ecommerce-ad-workflow` 负责 Product Truth、creative strategy 与 authoring package；
- AI-VIDEO Production Runtime 负责 canonical artifacts、Asset Registry、Manifest、Dependency Graph、`ResolvedTimeline`、Provider、composition、Review / Repair 与 Final Acceptance；
- `ProductionStateCommitter` 是唯一 Production write / activation / recovery owner；
- HyperFrames 是默认 Production renderer；
- Runtime source 不得导入、定位或调用 repository Skill。

## Executive Decision

AI-VIDEO 不需要重写现有 Production SDK。下一核心增量是新增一个薄而严格的 `EcommerceProductionJob` application layer，把已经存在但目前依赖测试或调用方手工拼装的能力连接成可恢复的生产流程：

```text
EcommerceAdProductionPackage
  -> Runtime-neutral Authoring Handoff
  -> Canonical Project Bootstrap / Reconciliation
  -> Reference And Shot Readiness
  -> Sequential Shot Generation
  -> Per-Shot Post-Media Gate
  -> Bounded Repair Or Explicit Recovery
  -> Canonical Composition And Render
  -> Whole-Video Ecommerce QC
  -> Final Acceptance
  -> Delivery Bundle
```

`EcommerceProductionJob` 不是第二个 workflow engine，也不保存第二套 mutable lifecycle。它只读取 canonical state、推导下一动作、调用现有 owner，并返回 machine-readable projection / blocker / result。

## Problem Statement

当前仓库已经具备大量 production primitives：strict `ProductionProject`、Asset Registry、content-addressed artifacts、Provider contracts、Shot readiness、generation feedback、per-Shot ecommerce gate、composition、audio/captions、P6 review、Final Acceptance 与 recovery。但完整电商广告生产仍缺一个真实 application owner：

- authoring package 到 Production artifacts 仍需要调用方手工编译和落盘；
- `run_ecommerce_ad_production()` 需要调用方预先构造 facade、compiled handoff、acceptance callbacks 与 render activation；
- per-Shot generation、repair、composition、whole-video QC 与 export 没有统一的 resume boundary；
- package、Project、Manifest、render 与 QA identity 之间没有一个 application request 明确绑定；
- final output 虽有 Gate，但没有 application flow 保证所有 required visual / semantic evidence 都已真实完成；
- 成片交付没有一个只允许 exact Final Accepted bytes 进入的 bundle contract。

结果是：单个组件可能正确，测试中的 happy path 也可闭合，但生产调用方仍可漏接 gate、误接旧 evidence、形成 silent fallback、整条重跑或在模型声称 `PASS` 后直接交付。

## Goal

提供一个 additive、Python-first、可恢复的 application contract，使一个已验证的电商广告 authoring package 能够：

1. 被 deterministic 地投影为 Runtime-neutral handoff；
2. 被编译为 canonical Production artifacts，而不是平行 artifact tree；
3. 在任意 interruption 后通过 canonical state 精确推导下一动作；
4. 逐 Shot 执行 generation、exact-byte Gate 与 bounded local repair；
5. 使用同一 `ResolvedTimeline` 完成 voice、captions、BGM / SFX、graphics 与 render；
6. 对 exact final MP4 执行 whole-video ecommerce QC 与 Final Acceptance；
7. 只把 Final Accepted bytes 与完整 provenance 打包为交付物。

## Non-Goals

- 不在本 slice 实现商品 URL crawler、OCR、catalog connector 或 automatic Product Truth extraction；
- 不新增 public CLI command、API server、queue service、database 或 frontend；
- 不改变 Legacy `ai-video validate/run/resume`；
- 不新增 Provider、renderer、timeline、Registry、Manifest、Dependency Graph 或 QA lifecycle；
- 不把 Skill package 变成 Runtime dependency；
- 不引入自动 campaign publishing、ad account、spend、ROAS 或 attribution；
- 不在 V1 实现 batch campaign、creative variant expansion 或 platform-specific multi-export；
- 不把 technical probe、Provider success、VLM score或局部 Gate 当作 Final Acceptance；
- 不授权 live Provider/media execution。真实媒体 qualification 需独立 accepted task 与现有 gates。

## Layering And Ownership

| Layer | Owns | Must Not Own |
| --- | --- | --- |
| `ecommerce-ad-workflow` | Product Truth、claims、audience、Hook、beats、CTA、creative package | Provider、Manifest、timeline、render、QA lifecycle |
| Handoff exporter | package/2 到 runtime-neutral bytes 的纯投影 | Production read/write、Provider、activation |
| Job compiler | handoff 到 existing artifact proposals / requirements 的纯编译 | direct filesystem mutation、lifecycle |
| `EcommerceProductionJobService` | reconcile、next-action、owner invocation、bounded stop | second state machine、hidden retry/fallback |
| Existing Production services | Registry、Manifest、generation、render、review、repair、recovery | ecommerce authoring truth |
| Delivery packager | exact accepted bytes + evidence inventory | re-render、mutation、acceptance decision |

## End-To-End Production Contract

```text
Package Validation
  -> Handoff Validation
  -> Project Bootstrap / Reconcile
  -> Asset And Reference Readiness
  -> Shot Execution Barrier (ordered)
       -> Generate Candidate
       -> Materialize Exact Bytes
       -> Per-Shot Gate
       -> PASS: activate exact candidate
       -> FAIL: classify and bounded repair
       -> NOT_EVALUATED: evidence repair first
       -> OUTCOME_UNKNOWN: stop for explicit recovery
  -> Composition Preflight
  -> Canonical Render
  -> Whole-Video Gate
  -> P6 Semantic Review
  -> Final Acceptance
  -> Delivery Bundle
```

每条箭头都是 explicit contract transition。不存在“尽力继续”、provider-dependent implicit behavior 或 fallback 到另一 renderer / provider / rubric。

## Contract 1: Runtime-Neutral Authoring Handoff

### Schema

`ecommerce-production-handoff/1`

### Required Fields

| Field | Meaning |
| --- | --- |
| `schema_version` | exact handoff schema identity |
| `handoff_id` | canonical SHA-256 of handoff payload excluding itself |
| `source_package_id` | exact `ecommerce-ad-workflow/package/2` package identity |
| `source_input_hash` | source authoring input identity |
| `delivery_profile` | `9:16`、duration、frame/audio intent、platform constraints |
| `product_truth` | fact/source/rights/claim references required by production |
| `artifact_proposals` | `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、ordered `Shot` proposals |
| `ad_creative_plan_proposal` | existing `AdCreativePlanProposal` projection |
| `asset_requirements` | product/reference/talent/set/logo/font/audio inputs and provenance requirements |
| `audio_caption_requirements` | VO/dialogue/TTS、caption、BGM、SFX、silence and ducking intent |
| `acceptance_requirements` | per-Shot and whole-video required findings, including final-output evidence |
| `unsupported_gaps` | classified non-executable package requirements |

### Rules

- Export is pure, deterministic, no-network and no-write.
- Same canonical package bytes MUST produce byte-identical handoff bytes.
- Any package `BLOCKER` or unresolved runtime capability MUST remain an explicit blocker; exporter MUST NOT silently omit it.
- Handoff contains no credential、permit、provider response、Manifest revision、active pointer or mutable status.
- Runtime validates the handoff using source code under `src/ai_video/production/`; it never imports `.agents/skills/**`.
- Skill-side exporter MAY import public runtime-neutral contract models, but Runtime source MUST remain unaware of Skill names and paths.

## Contract 2: Job Request

### Schema

`ecommerce-production-job-request/1`

### Required Fields

| Field | Meaning |
| --- | --- |
| `job_id` | stable operator/application identity, not mutable lifecycle |
| `project_root` | target Production Project root |
| `handoff_id` | exact authoring handoff |
| `expected_project_id` | prevents cross-project reuse |
| `execution_policy_id` | sealed routing/repair/render policy identity |
| `delivery_profile_id` | exact delivery constraints |
| `max_new_generation_attempts` | finite job-level ceiling |
| `max_repairs_per_shot` | finite local repair boundary |

Provider credentials、one-use permits、Budget Guard reservations and cloud-egress evidence stay in their existing owners. They are never embedded in the reusable job request.

## Contract 3: Job Projection

### Schema

`ecommerce-production-job-projection/1`

`EcommerceProductionJobProjection` is a read-only derivation from:

- exact request and handoff；
- reopened `ProductionProject` selected revision；
- Asset Registry selected snapshot；
- canonical Manifest lifecycle；
- Dependency Graph desired state；
- current Review / Repair / Final Acceptance receipts。

### Next Actions

| `next_action` | Required canonical evidence |
| --- | --- |
| `BOOTSTRAP_PROJECT` | no exact canonical project exists |
| `RECONCILE_PROJECT` | project exists but selected inputs differ safely |
| `PREPARE_REFERENCES` | required registered assets/references absent |
| `GENERATE_SHOT` | next ordered Shot has no accepted exact candidate |
| `REPAIR_SHOT_EVIDENCE` | required evidence is missing/stale/ambiguous |
| `REPAIR_SHOT_MEDIA` | known failed attempt has bounded repair available |
| `RECOVER_UNKNOWN_OUTCOME` | side-effect outcome is unknown |
| `PREPARE_COMPOSITION` | all Shots accepted but composition inputs unresolved |
| `RENDER_FINAL` | exact composition ready, no accepted current render |
| `REVIEW_FINAL` | current render exists but required whole-video evidence incomplete |
| `PACKAGE_DELIVERY` | exact final output accepted but not yet packaged |
| `COMPLETE` | delivery bundle verifies against accepted bytes |
| `BLOCKED` | no authorized safe automatic action exists |

These values are projections, not persisted lifecycle. Reopening the same canonical state MUST produce the same projection.

### Blocker Contract

`EcommerceJobBlocker` MUST include:

- stable `blocker_code`；
- existing typed `ErrorCode` where applicable；
- stage and exact subject identity；
- failure classification / diagnosis identity；
- evidence pointers；
- retryability derived from typed metadata；
- required owner/action；
- whether result is known or unknown。

It MUST NOT invent a parallel failure taxonomy when an existing typed production error, QA verdict or generation diagnosis already owns the meaning.

## Contract 4: Bootstrap And Reconciliation

- Compiler emits existing canonical artifact models and `PreparedArtifact` payloads; it does not write.
- Initial creation uses the public canonical `ProductionStateCommitter` bootstrap surface.
- Existing projects are reopened strict/read-only before reconciliation.
- Reconciliation may create new immutable revisions and update selected pointers only through existing writer contracts.
- Same request replay against already-matching state is side-effect free.
- Divergent content, stale revision, path escape, hash mismatch or ambiguous partial write fails closed.
- The Job does not create a second `job.json` lifecycle file. Durable truth remains in canonical Production artifacts and Manifest.

## Contract 5: Reference And Identity Readiness

Before a Shot can be submitted:

- product/reference assets are registered by exact measured bytes；
- required license/rights and Product Truth references are present；
- selected reference identities match the exact `AdCreativePlan` and Shot revision；
- protagonist/product continuity requirements are compiled into existing readiness contracts；
- provider capability selection satisfies the sealed requirement set；
- missing capability becomes `BLOCKED_CAPABILITY`, not a weaker silent path。

Provider switching is allowed only as an explicit new routing decision whose capability contract, bindings, permits and provenance are re-sealed. A new provider MUST NOT inherit an old provider's acceptance evidence.

## Contract 6: Ordered Shot Execution And Local Repair

- Shots execute in canonical Storyboard / `ResolvedTimeline` order.
- The next Shot MUST NOT submit until the prior Shot's exact materialized MP4 passes all required per-Shot findings.
- Tool/Provider success is only candidate production, never acceptance.
- `PASS` requires exact-byte, current-intent, current-revision evidence.
- `FAIL` invokes failure classification and only the bounded repair action allowed by the diagnosis.
- `NOT_EVALUATED` invokes `EVIDENCE_REPAIR_FIRST`; it MUST NOT regenerate media merely to hide missing evidence.
- `OUTCOME_UNKNOWN` stops and routes to explicit recovery; no blind retry or permit remint.
- Each media repair is a new exact attempt with new identity and full revalidation.
- Local repair MUST preserve already accepted product identity、continuity、timing、audio and narrative invariants. If the repair would degrade final-output quality, it is rejected.
- Exhausted attempt ceiling returns `BLOCKED`; it does not restart the whole pipeline.

## Contract 7: Composition And Final Render

The application layer prepares composition inputs but does not own timing or rendering semantics:

- one `ResolvedTimeline` remains the sole order/frame/sample/trim owner；
- voice/TTS、dialogue、captions、BGM、SFX、commercial graphics、CTA and end card bind to that timeline；
- `CompositionSpec` binds exact `AdCreativePlan` identity and exact accepted assets；
- HyperFrames remains default renderer；
- no renderer fallback is allowed；
- render output is materialized and hashed before review；
- a re-render is scoped to invalidated composition/render dependencies, not Shot generation, unless Dependency Graph says upstream media is stale。

V1 produces one final `9:16` master. Still/draft review stages, platform variants and batch campaign packs remain follow-up slices; their future introduction MUST reuse the same timeline, evidence and acceptance ownership.

## Contract 8: Whole-Video QC And Final Acceptance

Final QC is an AND-gate over the exact final MP4:

1. technical media validity；
2. universal visual/layout/timing/audio requirements；
3. ecommerce Product Truth、claim、product visibility、Hook、CTA and brand-closure requirements；
4. caption evidence when captions apply；
5. final-output contract observations for overall coherence, pacing, continuity, legibility and user-visible quality；
6. required human/independent evidence where automated evidence cannot establish the claim。

### No Bare-PASS Rule

- A model or callback returning `PASS` without required exact evidence MUST become `NOT_EVALUATED` or contract-invalid.
- A local metric cannot satisfy a different user goal. Lip-sync, OCR, loudness, duration or product similarity alone cannot prove the ad is acceptable.
- All required findings must pass. Aggregate score, majority vote or technical success cannot override a blocker.
- Evidence from another render hash, plan hash, project revision, provider attempt or rubric version is stale and rejected.
- Final Acceptance is recorded only through existing canonical review/committer surfaces.

## Contract 9: Delivery Bundle

### Schema

`ecommerce-delivery-bundle/1`

### Contents

- exact Final Accepted MP4；
- SHA-256 and media facts；
- project/registry/manifest selected identities；
- source package and handoff identities；
- accepted `AdCreativePlan`、Storyboard、Shots and composition identities；
- Provider/materialization provenance for generated assets；
- per-Shot Gate, repair and whole-video acceptance receipt pointers；
- delivery profile and export timestamp；
- machine-readable inventory manifest。

Packaging is read-only with respect to Production lifecycle. It copies or links only verified accepted bytes into a temporary bundle, verifies the inventory, then atomically publishes the bundle. It MUST NOT re-encode the video, make a new acceptance decision or mutate active pointers.

## Resume And Replay Semantics

- `resume` is implicit in every Job service invocation: reopen, validate, project, execute at most the requested bounded action.
- Exact replay performs no Provider, render, analyzer, materializer or Manifest write side effect.
- Known incomplete state resumes from the smallest invalid frontier.
- Unknown outcome never becomes known through inference; explicit recovery must inspect durable intent and side-effect evidence.
- Completed Shots are not regenerated when only audio/caption/composition/final review is invalid.
- A final review failure does not invalidate accepted Shots unless the diagnosis identifies an upstream Shot defect and Dependency Graph derives that frontier.

## Application API Shape

The implementation MAY refine names, but MUST preserve these semantics:

```python
service = EcommerceProductionJobService(
    request=request,
    handoff=handoff,
    dependencies=dependencies,
)

projection = service.inspect()
result = service.advance_once(expected_action=projection.next_action)
```

`inspect()` is strict, read-only and no-network. `advance_once()` executes one bounded application action and returns reopened canonical projection. A separate convenience `run_until_blocked()` MAY loop over actions, but only with finite task ceilings and the same explicit barriers.

## Compatibility And Migration

- All new schemas are additive `/1` contracts.
- Existing Production projects, manifests, artifacts and Legacy runs require no migration.
- Existing `run_ecommerce_ad_production()` remains behavior-compatible and becomes a lower-level delegate, not a competing public workflow.
- Existing test facades remain valid.
- No new runtime dependency is required.
- Public CLI is unchanged. A future CLI/API surface requires separate explicit approval and contract work.
- Removing the new application modules leaves existing primitives operational; no existing state is rewritten solely to opt in.

## Security And Authorization

- Handoff and request contain secret references only where existing contracts allow; never raw credentials.
- Read-only inspection performs no network, upload, Provider submit or state write.
- Remote/paid actions still require current task authorization and all existing Budget Guard、cloud-egress、durable intent and one-use permit gates.
- Local ComfyUI retains its existing authorization exemption but not an exemption from identity、intent、provenance、repair or media gates.
- Attempt ceilings are finite and cannot be expanded by fallback logic.

## Observability And Provenance

Every action result must bind:

- job/request/handoff identity；
- project, registry and manifest revisions before and after；
- action name and owner；
- exact input/output hashes；
- side-effect intent / permit / receipt identities when applicable；
- typed outcome and blocker；
- dependency invalidation / rebuild frontier；
- timestamp and actor/tool identity。

This evidence is stored through existing canonical artifacts/receipts. The Job projection only references it and does not become another ledger.

## Acceptance Criteria

1. `package/2` fixture exports deterministically to a schema-valid handoff with exact identity binding.
2. Runtime source contains no Skill import, path, loader or identity.
3. Compiler produces schema-valid existing Production artifact proposals and rejects unmapped blocker/gap fields.
4. Initial bootstrap uses the canonical committer and exact replay produces no write.
5. `inspect()` is strict, no-network and side-effect free.
6. Projection is derived solely from canonical state and is stable across reopen.
7. Sequential execution prevents Shot N+1 submit until Shot N exact-byte Gate passes.
8. `FAIL`、`NOT_EVALUATED` and `OUTCOME_UNKNOWN` take distinct, tested paths.
9. Repair is bounded, creates a new attempt identity and resumes only the invalid frontier.
10. Provider switching cannot reuse old bindings, permits, media evidence or acceptance.
11. Composition consumes the exact accepted assets and one canonical `ResolvedTimeline`.
12. Voice/TTS、captions、BGM/SFX、CTA and end card are either resolved or explicit blockers before render.
13. Whole-video QC rejects bare `PASS`, stale evidence and partial rubric coverage.
14. Final Acceptance binds exact render bytes, current plan and current project revision.
15. Delivery packaging refuses non-accepted or hash-mismatched output and never re-encodes it.
16. Interruption at every external side-effect boundary resumes safely without duplicate side effects.
17. Existing Legacy CLI and Production APIs remain compatible.
18. Targeted tests, full applicable suite, Architecture Gate and exact-snapshot Harness pass.
19. Live Provider/media quality remains explicitly unverified until a separately authorized exact-media acceptance run is completed.

## Deferred Follow-Up Specs

The following are intentionally separate contracts after V1 closure:

- Product URL / catalog ingestion and Product Truth extraction；
- staged Still -> Draft -> Final review economics；
- platform-specific variants and one-variable creative matrix execution；
- batch / campaign pack scheduling；
- public CLI/API/queue surface；
- empirical model/provider qualification matrix。

Deferral prevents `EcommerceProductionJob` from becoming a God Module while preserving clear extension seams.
