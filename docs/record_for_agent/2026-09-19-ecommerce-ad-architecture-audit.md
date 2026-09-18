---
record_kind: research_note
topic_id: ecommerce-ad-production-architecture
learning_eligibility: ineligible
---

# Ecommerce Ad Production Architecture Audit Record

Date: 2026-09-19

## Purpose

记录当前 AI-VIDEO 相对“电商广告视频全自动生产”目标的 source-level 架构边界，以及五个外部开源项目中值得吸收但不能直接替代本仓库 canonical owners 的设计。

完整审计、比较矩阵、P0/P1/P2 gaps、target architecture 与 Harness proposal 位于：

- `docs/research/2026-09-19-ecommerce-ad-production-architecture-audit.md`

本记录不授权 implementation、Provider/media execution、Production state mutation、release 或 quality acceptance。

## Current Runtime Truth

审计基于 dirty local checkout `ae272598eecb49591c522aa690b7ad36a15b81b4`。当前真实边界是：

- Public `ai-video` CLI 仍只进入 Legacy `PipelineRunner`，没有接入 v0.2 ecommerce/P6/Final Acceptance。
- v0.2 Production 已有 strict artifacts、provider capability routing、durable generation、exact-byte provenance、single-writer activation/recovery、`ResolvedTimeline`、HyperFrames、per-Shot barrier 与 whole-video acceptance lifecycle。
- `run_ecommerce_ad_production()` 是受测 Python API，但仓库内 non-test packaged application caller 不存在；caller 必须提供 compiled handoff、per-Shot facades、render callback 与 QA/evaluator callbacks。
- `ecommerce-ad-workflow` 的 `EcommerceAdProductionPackage` 是丰富的 authoring contract，不是 Product Runtime state；当前没有 canonical compiler 将其自动变成 `ProductionBrief`、`Story`、`Storyboard`、`Shot` 与 `AdCreativePlan`。
- 电商最低 domain finding 只含 `requirement_id`、`verdict`、`rationale`。仓库已有更强的 final-output visual/human observations，但 ecommerce closure 未把该 contract 设为 mandatory；caption-quality 在 timeline 有 captions 时已强制执行。问题是 final-output wiring/policy gap，不是所有 Final Acceptance contract 都可被 bare PASS 绕过。
- Failure diagnosis、attempt history、quota、intervention 与局部 invalidation 已存在；没有 canonical application driver 自动执行 bounded repair-to-acceptance loop。
- Voice、captions、BGM/SFX mix 与 deterministic assembly 是真实 runtime primitives；从 sealed ad script 到最终音频/字幕/CTA/成片的广告级 application orchestration 尚未闭合。
- Platform variants 与 campaign batch 目前只有 authoring/局部工具，不存在 durable production executor。

## External Research Snapshot

外部 source review 绑定以下 commits：

- `SamurAIGPT/Generative-Media-Skills@5519622e885abc60217a65c8e090bcb1d9830746`
- `YILS-LIN/short-video-factory@7f66665a33bfe30ed76598846158cf512f93d01f`
- `Anil-matcha/Open-AI-UGC@9fffcc1a9518ea9b07ce8947891141a8aa2bf418`
- `leosssvip-dot/remotion-ad-video-skill@e734c0299474132366e8270e9cffaf9a26f2c5ed`
- `AtlasCloudAI/atlas-marketing-studio@18ec178052f6f97612813997613d88ce34b02fc5`

Durable takeaways：

- 吸收 `Generative-Media-Skills` 的 Core/Library 分层、small composable tools 与 provider input catalog；Production truth 继续由 AI-VIDEO runtime 独占。
- 吸收 `remotion-ad-video-skill` 的 `Brief -> Assets -> Storyboard -> Still -> Draft -> QA -> Final` operator lifecycle，但每一步必须映射到现有 Manifest/Dependency/Review owners 与 hash-sealed receipts。
- 吸收 `short-video-factory` 的 narration-driven timeline、TTS/SRT、subtitle rendering、BGM loudness 与 cancellable composition UX；不吸收随机 visuals、无 lineage/QC 的路径。
- 吸收 Atlas 的 polling resume、transient/terminal distinction、atomic completion 与 idempotent compensation；不吸收 automatic generic fallback、hard-coded workflow 或 URL-only lineage。
- Open-AI-UGC 主要可参考 authenticated creation history 与 upload UX；submit-before-durable-row、weak webhook/completion semantics 不适合作为 control-plane 设计。

## Verification And Evidence

- Codegraph 查询确认 `run_ecommerce_ad_production()` 的模块内/test callers，以及 `run_ecommerce_ad_generation()` 的 call relationships。
- Exact `rg` search 未找到 packaged non-test application caller，也未找到 Product URL -> ProductTruth runtime extractor。
- Focused ecommerce/ad-gate suite：`77 passed in 63.83s`。
- Ecommerce authoring/composition/captions/generation-feedback suite：`237 passed in 11.52s`。
- 没有 live Provider submit、media generation、media viewing 或 human quality acceptance。

## Recommended Evolution Boundary

优先建立薄的 `EcommerceProductionJob` application owner：

```text
ProductInput -> ProductTruth -> AdBrief -> CreativeConcept -> Script
-> Storyboard -> ShotSpec -> ReferenceAsset -> VideoGeneration
-> ShotQC -> Assembly -> FinalQC -> VariantGenerator -> Export
```

该 owner 只负责编排和 stage transition，不改变下列 canonical ownership：

- `ProductionStateCommitter` 仍是唯一 writer。
- Dependency Graph 仍独占 invalidation/rebuild frontier。
- `ResolvedTimeline` 仍独占 order/frame/sample/timing。
- HyperFrames 仍是默认 renderer。
- Provider adapter、Skill、Agent、subagent 与 analyzer 都不能直接 activation 或 Final Acceptance。

## Agent Guardrails

- 不要把本审计的 target architecture 描述成当前 runtime truth。
- 不要把 focused tests 推广为 live media/model quality proof。
- 不要把 exact-byte binding 误写为 semantic correctness proof。
- 不要新建第二个 job Manifest、timeline、renderer、failure taxonomy 或 activation owner。
- Development Harness 继续验证 code changes；未来 Production Harness 负责编排 media job。两者 receipt 不能互相替代。
- Atlas plan fallback 是显式 `fallback: true` 的 automatic template fallback；它的问题是 non-fail-closed，不是 silent。
