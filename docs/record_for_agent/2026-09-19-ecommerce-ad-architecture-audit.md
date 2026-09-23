---
record_kind: research_note
topic_id: ecommerce-ad-production-architecture
learning_eligibility: ineligible
---

# Ecommerce Ad Production Architecture Audit Record

Date: 2026-09-19

## Supersession Notice — 2026-09-24

下方“M4–M6 仍未实现”等结论是 2026-09-19 架构审计时的历史状态。
M0–M7 offline application implementation 现已提交至 `f4f0dc4`；当前精确
验证与未验收边界见 [M7 Offline Code Record](2026-09-19-ecommerce-production-job-m7-offline-code.md)。
这不证明真实商品广告的视觉质量或 live Production delivery。

## Supersession Notice — 2026-09-19

下文 `Specification And Plan Checkpoint` 中“只有文档与设计证据”已被
[Ecommerce Production Job M0–M3 Implementation Record](2026-09-19-ecommerce-production-job-m0-m3.md)
部分取代。M0–M3 现已实现 strict handoff/request/projection contracts、四层精确视觉合同、
Skill-side pure exporter、canonical compiler/bootstrap adapter 与 read-only `inspect()`，并在 exact
commit snapshot 上通过 Harness。原审计的历史 gap 与 target architecture 仍保留；M4–M6 Provider/media、
repair、render、Final Acceptance 和 delivery packaging 仍未实现，也没有视觉成片验收。

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

## Specification And Plan Checkpoint

本次后续工作把上述审计结论收敛为两个 proposed、docs-only contracts：

- `docs/superpowers/specs/2026-09-19-ai-video-ecommerce-production-job.md`
- `docs/superpowers/plans/2026-09-19-ai-video-ecommerce-production-job.md`

核心架构决定：

- 下一 slice 是薄的 `EcommerceProductionJob` application layer，不重写 Production SDK，也不继续扩张已经较大的 `ecommerce_ad_coordinator.py`。
- `ecommerce-ad-workflow/package/2` 先导出 versioned、runtime-neutral handoff；`src/` Runtime 继续禁止导入或调用 Skill。
- Job request 是 immutable execution intent；Job projection 只从 Project / Registry / Manifest / Dependency / Review canonical state 推导，不持久化第二套 lifecycle。
- 应用层使用 `inspect()` 和 bounded `advance_once()` 语义，精确恢复最小 invalid frontier；unknown outcome 仍必须 explicit recovery。
- Shot generation 保留 sequential per-Shot exact-byte barrier；`FAIL`、`NOT_EVALUATED` 与 unknown outcome 分别进入 media repair、evidence repair 与 recovery，禁止 blind retry。
- composition 继续只消费一个 `ResolvedTimeline` 并使用 HyperFrames；voice/TTS、captions、BGM/SFX、CTA 与 end card 必须在 render 前解析或成为 blocker。
- whole-video QC 必须拒绝无 required evidence 的 bare `PASS`；delivery bundle 只接受 exact Final Accepted MP4，不重新编码、不改变 activation。
- V1 明确不包含 Product URL crawler、batch/variants、public CLI/API、campaign publishing 或 live Provider qualification；这些需要独立 follow-up spec 和授权。

Implementation plan 分为 contract guards、handoff、compiler、projection/resume、Shot/repair、composition/render、final QC/delivery 与 offline E2E 八个 milestones。推荐首个 implementation slice 只执行 Milestone 0–3，使 application boundary 先稳定，再单独审查 Provider/media、repair、render 与 Final Acceptance integration。

该 checkpoint 只有文档与设计证据，不证明 `EcommerceProductionJob` 已实现、可运行或已通过真实媒体质量验收；本轮没有 Provider submit、媒体生成、Production state mutation、push 或 release。

## Agent Guardrails

- 不要把本审计的 target architecture 描述成当前 runtime truth。
- 不要把 focused tests 推广为 live media/model quality proof。
- 不要把 exact-byte binding 误写为 semantic correctness proof。
- 不要新建第二个 job Manifest、timeline、renderer、failure taxonomy 或 activation owner。
- Development Harness 继续验证 code changes；未来 Production Harness 负责编排 media job。两者 receipt 不能互相替代。
- Atlas plan fallback 是显式 `fallback: true` 的 automatic template fallback；它的问题是 non-fail-closed，不是 silent。
