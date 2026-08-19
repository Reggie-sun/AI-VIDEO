# AI-VIDEO Shot Continuity Implementation Plan

## Status

本文档最初是上述 Shot Continuity specification 的 proposed implementation plan。2026-08-19后续明确执行请求已完成Milestone 1-5、Hailuo 2.3/Seedance 2.0 Mini offline portions与provider-neutral technical suites；Manifest 2.8 / terminal PNG Registry activation属于另行明确授权的scope expansion。Local MiniMax H3因缺sealed complete workflow/profile保持pending；Milestone 9-10的Provider live与subjective acceptance未执行。没有调用Provider、重新生成媒体、push或release。

## Objective

在不复制 timeline、renderer、state writer、P5 resolver 或 Agent runtime 的前提下，把 Shot N 的 exact activated terminal-frame state 变成 Shot N+1 可验证的 `first_frame` continuity input，并为 local continuity、MiniMax cloud Hailuo 2.3 与 Seedance 2.0 Mini 建立互不混淆的 capability-gated lane。

## Problem Boundary

- `single timing owner`: `ResolvedTimeline`。
- `single durable/activation/recovery owner`: `ProductionStateCommitter`。
- `single invalidation owner`: 既有 P5 graph builder/resolver/selective rebuild。
- `single render owner`: 既有 HyperFrames renderer。
- `old path to retire`: 只在 continuity-enabled Shot 上禁止“没有 exact upstream binding 的独立生成”路径；普通 P8 T2V/I2V 和非 continuity Shot 不退役。
- `unchanged contracts`: P3/P4 audio/captions/mux、Legacy CLI/layout、static-image、existing generated-MP4 compatibility、default no-network、Paid Provider Gate。
- `focused verification`: 以 P8 request/activation E2E、P5 selective rebuild、P3/P4 composition/HyperFrames 和 provider adapter tests 为主；任何 live proof 单独授权。

## Entry Gates

Implementation 开始前必须同时满足：

1. 用户单独授权 implementation；本 docs-only approval 不复用。
2. 工作区 writer ownership 清晰，目标 files 无 overlapping uncommitted work。
3. “MiniMax 本地”解析为 exact engine/model/workflow/profile/endpoint；若不能证明 loopback local execution，则不建立该 lane。
4. MiniMax Hailuo 2.3 与 Seedance 2.0 Mini 的 official capability snapshots 刷新并保存可审计出处。
5. 对 terminal evidence 是否能在现有 schema/layout 内 durable reopen 完成 bounded executable spike；若不能，先停下提交独立 scope-expansion spec。

## Milestone 1: Freeze Provider-Neutral RED Contracts

### Target Surface

- `src/ai_video/production/video.py`
- `src/ai_video/production/video_contracts.py`
- `tests/test_production_video.py`

### Work

先写 failing tests，固定 `ContinuityConstraintSet`、`TerminalFrameEvidence` 和 `ContinuityReferenceBinding` 的 canonical fields/hash 语义。选择向后兼容的 extension/composition seam，使旧 `VideoGenerationRequest` 和旧 request/resolved hash fixtures保持稳定。

RED cases 至少包括：

- binding 缺 source Shot/candidate/video asset/evidence/constraints 任一 identity 时拒绝；
- extracted image hash 或 upstream candidate hash 改变时 request desired fingerprint 改变；
- generation instance identity 变化不破坏既有 exact replay 语义；
- wrong target Shot/revision、wrong role、duplicate binding 和 non-canonical ordering 拒绝；
- continuity-enabled request 不能使用 T2V mode 或空 `first_frame`。

### Verification

```bash
pytest -q tests/test_production_video.py
```

## Milestone 2: Implement Capability-Gated Resolution

### Target Surface

- `src/ai_video/production/video.py`
- `src/ai_video/production/video_contracts.py`
- `tests/test_production_video.py`

### Work

复用 `VideoCapabilityVariant` 与 `ResolvedVideoGenerationRequest`。Provider adapter construction、`capabilities()` 和 `resolve()` 必须无外部副作用；continuity request 的 mode/role/MIME/size/dimension/output coupling 必须在 `preview`、durable submit intent 和任何 Provider external effect 前 fail closed。若需要表达 terminal evidence lineage，扩展 resolved request hash，而不是在 adapter 中读取任意 path。

必须保留：

- unsupported capability 返回 typed `VIDEO_CAPABILITY_UNSUPPORTED`；
- submit call count 为零；
- 无 T2V、prompt-only 或 remote fallback；
- provider-specific fields 不进入 core contract。

### Verification

```bash
pytest -q tests/test_production_video.py
```

## Milestone 3: Seal Terminal-Frame Evidence

### Target Surface

- `src/ai_video/production/video_artifact.py`
- `src/ai_video/production/_state_commit_video_candidate.py`
- `src/ai_video/production/state_commit.py`
- `tests/test_production_video.py`
- `tests/test_production_generated_video_e2e.py`
- `tests/test_production_video_state_recovery.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`

### Work

以 strict RED-first tests 定义 source video measured metadata、terminal frame selection、held-FD extraction、image measured validation、canonical extraction receipt 和 evidence hash。Extraction 必须读取 exact source bytes，并把 source Shot/candidate/generation/Registry/provenance 全部 seal。

优先复用现有 immutable artifact/provenance seam，不改变 public layout。Scratch file 只存在于 transaction 内，不能成为 durable reference。

### Scope-Expansion Stop Gate

若 executable spike 证明以下任一项不可避免，立即停止实现并请求独立授权：

- 一个 candidate transaction 必须 append 第二个 active Registry asset；
- Manifest 必须增加 terminal-frame pointer/lifecycle；
- artifact layout 必须新增 public directory contract；
- video activation 从“exactly one appended asset”变成 multi-asset activation。

该授权必须带 schema versioning、legacy reopen、crash matrix、migration/rollback 和 contract-matrix 更新。本 plan 不预先批准它。

### Verification

```bash
pytest -q \
  tests/test_production_video.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py
```

## Milestone 4: Extend Durable Activation and Recovery

### Target Surface

- `src/ai_video/production/_state_commit_video_candidate.py`
- relevant private `_state_commit_*` transaction helpers
- `src/ai_video/production/state_commit.py`
- `tests/test_production_generated_video_e2e.py`
- `tests/test_production_video_state_recovery.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`

### Work

由 `ProductionStateCommitter` façade共同提交 terminal evidence、source candidate binding、downstream request receipt 和 existing Project/Registry/graph activation。为以下 crash point 添加 fixtures：

- fetched video 已 durable、尚未 extraction；
- extracted evidence 已 durable、尚未 candidate preparation；
- candidate 已准备、尚未 activation；
- activation commit point 前后；
- recovery reopen 时 evidence tampered/unreadable/wrong source。

Exact replay 必须不重复 fetch、extract、candidate preparation、activation 或文件写入。若 Provider effect 已发生，recovery 继续使用 existing attempt/receipt，不得 resubmit。

### Verification

```bash
pytest -q \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py
```

## Milestone 5: Add P5 Continuity Dependency

### Target Surface

- `src/ai_video/production/dependency.py`
- `tests/test_production_dependency.py`
- `tests/test_production_selective_rebuild.py`
- activation E2E fixture that builds the graph

### Work

先用 failing graph tests 固定一个 typed, allowlisted continuity edge：source terminal evidence N 到 generated visual asset N+1。不得把 source change 映射到 Shot N+1 authoring artifact，也不得用 Shot 顺序循环生成 blanket edges。

Test matrix：

- source candidate bytes 改变，只 stale N+1 output 和真实 composition/render closure；
- terminal selection/evidence 改变，closure 相同；
- Shot N+1 continuity constraints 改变，stale N+1 output；
- N+2 只有存在显式 N+1→N+2 continuity edge时才 transitive stale；
- unlinked later Shots、voice、captions 和 unrelated assets保持 fresh；
- same desired failure保持 failed/blocked；
- exact replay 无 execution unit/state advance；
- graph 不保存 timeline 或 mutable lifecycle duplicate。

如果需要新增 edge enum/reason，必须保持 graph strict validation 和旧 snapshot reopen compatibility；若需要 graph/Manifest schema bump，则触发独立 scope-expansion gate。

### Verification

```bash
pytest -q \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_generated_video_e2e.py
```

## Milestone 6: Implement Provider Lanes Separately

Provider lanes必须在 provider-neutral core、Fake E2E 和 P5 gates通过后分别实现。一个 lane 的证据不能替代另一个 lane。

### Lane A: Local Continuity

先解析用户所称 “MiniMax 本地” 的真实 identity：

- 若为 Wan + ComfyUI：建立独立、loopback-only、exact workflow/profile binding 的 local video adapter；不得把它命名为 MiniMax Provider。
- 若为一个真实 local MiniMax-compatible runtime：要求 exact binary/server/model/checkpoint/API contract 和 loopback proof，再决定 adapter name。
- 若底层仍访问 MiniMax cloud：归入 Lane B，并受 Paid Provider Gate 和 Cloud Egress 约束。

任何 local adapter 都必须无 remote fallback、默认不联网，并以 Fake/sealed loopback tests证明 `first_frame` exact bytes进入 workflow binding。新 `ComfyUIVideoProvider` 本身若超出现有 P8 approved adapter scope，需要独立 implementation authorization。

### Lane B: MiniMax Cloud Hailuo 2.3

Target surface：

- `src/ai_video/production/minimax_hailuo.py`
- `tests/test_production_minimax_hailuo.py`

基于 refreshed official profile，新增 `MiniMax-Hailuo-2.3` I2V variant和 `first_frame_image` mapping。Tests 必须检查 exact model、image encoding/reference、duration/resolution coupling、sanitized failures、authorization/permit、submit-once 和 unsupported last-frame denial。不得因其他 Hailuo model 有 first/last-frame API 就把该能力外推到 2.3。

Offline verification：

```bash
pytest -q tests/test_production_minimax_hailuo.py tests/test_production_video.py
```

### Lane C: Seedance 2.0 Mini

Target surface：

- `src/ai_video/production/seedance_capabilities.py`
- `src/ai_video/production/seedance.py`
- `tests/test_production_seedance.py`

刷新 `doubao-seedance-2-0-mini-260615` official capability snapshot，验证 I2V first-frame 与 optional last-frame 的 exact content payload、MIME/geometry、audio opt-out、profile fields、response/fetch mapping、sanitized failures 和 authorization/permit。Current capability table 的声明不是 live proof，不能仅靠 fixture pass 宣称 provider acceptance。

Offline verification：

```bash
pytest -q tests/test_production_seedance.py tests/test_production_video.py
```

## Milestone 7: Prove End-to-End Without Live Calls

### Target Surface

- `tests/test_production_generated_video_e2e.py`
- `tests/test_production_composition.py`
- `tests/test_production_hyperframes.py`
- relevant Fake Provider fixtures

### Work

构造至少三 Shot 的 local Fake chain：N terminal evidence作为 N+1 first-frame binding，N+1 terminal evidence作为 N+2 binding。证明 submit/fetch/extract/activate/recovery/P5 closure，并把 activated MP4 送入现有 composition path。

Composition/HyperFrames tests只验证 unchanged invariants：exact trims、frame/sample boundaries、video element binding、audio/caption mix和 final mux request。它们不得以 crossfade或渲染结果伪装 Provider conditioning proof。

### Verification

```bash
pytest -q \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py
```

## Milestone 8: Technical Acceptance and Harness

运行 policy/contract matrix 对 P8 Provider lifecycle 要求的完整 safety/recovery集合，再叠加本 slice 的 P5 和 P3/P4 suites；并按 `.agent/harness/policy.yaml` 对 exact staged delta执行 fresh Harness。任何 code/tooling change 必须生成并校验 fresh receipt。下列命令是当前计划基线；实际 changed paths 若触发更多 Harness checks，以 policy 结果为准。

```bash
pytest -q \
  tests/test_production_paid_provider.py \
  tests/test_production_paid_provider_state.py \
  tests/test_production_paid_provider_e2e.py \
  tests/test_production_video.py \
  tests/test_production_video_fake.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_minimax_hailuo.py \
  tests/test_production_seedance.py

git add <exact-task-files>
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
```

Technical acceptance report必须列出 tests、Harness receipt、artifact hashes、exact replay counters、recovery points 和 P5 affected-node sets；不能写成 provider live或 subjective quality已通过。

## Milestone 9: Separately Authorized Provider Live Proof

本 milestone 只有在用户以 task-scoped request 明确列出允许执行的 provider/model、预算和调用边界后才能执行，并且每个 remote lane使用独立 Budget Guard/Cloud Egress/bounded-call plan。一条请求可以同时授权其中明确列明的多个 lane；不得把 docs-only approval、旧 diagnostic 或未列明的 provider当作授权。

每个 lane 的 live proof至少证明：

- exact provider/model/profile/capability snapshot；
- Shot N terminal evidence hash 等于 submit payload 消费的 first-frame bytes；
- exactly bounded submit/status/fetch，replay新增零调用；
- fetched MP4 measured validation、terminal evidence、candidate activation和 reopen/recovery；
- provider cost/budget receipt完整；
- 不把一次 lane success 外推到其他 lane。

重新生成 Shot 2/3属于新的本地执行或付费调用。它不在本 docs-only task授权范围内，也不能由旧 P8/Hailuo/Seedance diagnostic授权覆盖。

## Milestone 10: Subjective Continuity Acceptance

在 live proof之后，为每条 continuity edge生成未加转场的 terminal/initial pair和最终序列。分别执行：

- local `video-analysis`：scene/character identity、camera direction、motion direction、lighting/color、entrance/exit和spatial relation逐项报告；
- blinded human review：使用预先冻结的 rubric，对同一维度评分并给出 blocking discontinuity；
- Provider/lane comparison：local、Hailuo 2.3、Seedance 2.0 Mini分别报告，不混合平均掩盖失败。

Subjective acceptance必须独立于 technical和live verdict。单一相似度、crossfade后观感或 prompt 文案一致均不足以通过。

## Documentation Closure

实现真正完成后，才更新 runtime baseline、roadmap、primary contract matrix、README/AGENTS 中必要的 runtime truth，并清楚记录：

- provider-neutral contract已实现范围；
- 每个 provider lane的offline/live/quality状态；
- schema/layout是否保持不变；
- Harness receipt、local evidence与未授权 lane；
- rollback和known limitations。

原 P8 provider spec保持历史和当前 provider contract，不被重写成 continuity spec。

## Final Definition of Done

`provider-neutral technical implementation complete` 只表示 provider-neutral request/evidence、durable lifecycle、P5 precise invalidation、P3/P4 invariants 和 fresh Harness 已通过；它不得暗示任何 provider live或quality acceptance。

只有以下条件同时满足，才能称本计划要求的 `three-lane Shot Continuity acceptance complete`：

- request/reference/provenance binding executable tests通过；
- tamper/unreadable/capability denial fail closed；
- durable activation/recovery与exact replay通过；
- P5 precise invalidation只影响真实 closure；
- P3/P4、static-image、Legacy、no-network和generated-MP4 compatibility无回归；
- fresh Harness receipt验证成功；
- local continuity、MiniMax cloud Hailuo 2.3 和 Seedance 2.0 Mini 三条 lane 都已解析为 exact runtime/model/profile，并在 task-scoped authorization 下分别完成 live proof；
- subjective continuity review单独通过。

任一 lane 未完成 exact identity resolution、被 capability denial、未获授权或未通过 live proof时，three-lane acceptance 必须保持 `pending` 或 `blocked`，不能由另一 lane 的成功代替。若仅完成前六项，必须报告为 `provider-neutral technical acceptance only`，不得称 live、three-lane 或 quality accepted。
