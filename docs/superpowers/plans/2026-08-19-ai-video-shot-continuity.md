# AI-VIDEO Shot Continuity Implementation Plan

## Status

本文档最初是上述 Shot Continuity specification 的 proposed implementation plan。2026-08-19后续明确执行请求已完成Milestone 1-5、Hailuo 2.3/Seedance 2.0 Mini offline portions、provider-neutral technical suites，以及Milestone 6 Lane A的Local MiniMax H3 `fl2va` sealed workflow/profile、loopback-only adapter与durable local lifecycle；Milestone 9的C1 Local H3 lane也已完成。2026-08-20 separately authorized Alice C2 tasks完成shared terminal/keyframe prerequisite；首个Hailuo result收敛adaptive geometry但其receipt migration不计canonical lifecycle，随后新bounded adaptive request完成one-submit/fetch/activation/recovery/replay，human visual review为`pass with minor concerns`。Lane C Seedance完成exact resolve与fresh `3 CNY` preview，但因缺少Ark registered asset materialization在POST前fail closed，submit count为零。Local H3 C2 Shot 2、Seedance live、`ref2va`、blinded three-lane acceptance与Router仍pending；没有push或release。

2026-08-22本plan继续作为唯一Shot Continuity execution owner，并增加`C4_MULTI_ANCHOR_MOTION_CONTINUITY` ordered implementation lane。C4 spec已冻结，implementation尚未开始。v7在full-speed user review后因identity与camera-motion discontinuity被明确拒绝，fetched Seedance artifact保持unactivated；历史reviewer `accept with concerns`、SSIM与Provider success不构成C4 acceptance。本轮authority只覆盖本spec/plan更新，不覆盖runtime code、media generation、paid preview/POST或permit。

## Objective

在不复制 timeline、renderer、state writer、P5 resolver 或 Agent runtime 的前提下，把 Shot N 的 exact activated terminal-frame state 变成 Shot N+1 可验证的 `first_frame` continuity input，并为 local continuity、MiniMax cloud Hailuo 2.3 与 Seedance 2.0 Mini 建立互不混淆的 capability-gated lane。

新增C4 objective：把first-frame-only continuity升级为同一generation同时消费exact terminal、canonical identity、approved endpoint与exact upstream motion tail的multi-anchor contract，并将static boundary acceptance与motion boundary acceptance分别验收。任何Provider在无法证明完整mixed capability时必须在paid preview/POST前fail closed。

## Problem Boundary

- `single timing owner`: `ResolvedTimeline`。
- `single durable/activation/recovery owner`: `ProductionStateCommitter`。
- `single invalidation owner`: 既有 P5 graph builder/resolver/selective rebuild。
- `single render owner`: 既有 HyperFrames renderer。
- `old path to retire`: 只在 continuity-enabled Shot 上禁止“没有 exact upstream binding 的独立生成”路径；普通 P8 T2V/I2V 和非 continuity Shot 不退役。
- `C4 old path to retire`: 对显式C4 attempt，退役exact-terminal Router只投影`("first_frame",)`以及continuity validator只接受`first_frame + optional last_frame`的路径；C1/C2/C3与ordinary P8 paths保持不变。
- `unchanged contracts`: P3/P4 audio/captions/mux、Legacy CLI/layout、static-image、existing generated-MP4 compatibility、default no-network、Paid Provider Gate。
- `focused verification`: 以 P8 request/activation E2E、P5 selective rebuild、P3/P4 composition/HyperFrames 和 provider adapter tests 为主；任何 live proof 单独授权。

## Entry Gates

Implementation 开始前必须同时满足：

1. 用户已单独授权本次Local H3 implementation、compatible Manifest/local evidence expansion和bounded live-local proof；该授权不复用于cloud/paid lane。
2. 工作区 writer ownership 清晰，目标 files 无 overlapping uncommitted work。
3. “MiniMax 本地”的engine/model/loopback identity已解析为本机ComfyUI + native MiniMax H3，并已seal exact checkpoint hashes、complete workflow/binding/profile、node inventory和output contract；raw smoke JSON没有升级为production profile。
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

当前identity已解析并seal为本机ComfyUI native MiniMax H3 `fl2va`，不是Wan或MiniMax cloud。Production template由pinned Comfy-Org official UI/subgraph workflow reviewed/export，而非raw smoke节点图；sealed profile固定ComfyUI commit、四组件、native nodes、loopback endpoint、24fps、17k+5 frame-grid、124-362 trained frame boundary、native audio和MP4 bounds。

Target surface：

- Add `src/ai_video/production/comfy_video.py` — loopback-only `ComfyUIVideoProvider` transport、preflight、submit/poll/history/fetch mapping；不得复用cloud `MiniMaxH3VideoProvider`或Paid Provider permits。
- Add `workflows/templates/minimax_h3_fl2va_api.json` — 从pinned Comfy-Org official UI/subgraph workflow reviewed/export而来，不得把14-node ad-hoc raw smoke JSON直接提升为production template。
- Add `workflows/bindings/minimax_h3_fl2va_binding.yaml` — exact `prompt`、`first_frame`、optional explicit `last_frame`、`seed`、`width`、`height`、`length`/`frame_count`、`steps`/`sampler`与`output_prefix` binding。
- Add `workflows/profiles/minimax_h3_fl2va.json` — seal upstream provenance、derived workflow/binding、runtime/components/nodes/endpoints与output/resource bounds。
- Optional add独立`minimax_h3_ref2va` template/binding/profile — 只有角色/场景reference acceptance需要时才进入；不得与`fl2va`共用checkpoint/profile identity。
- Add `tests/test_production_comfy_video.py`与`tests/test_production_local_video_state.py` — sealed profile/preflight、exact first-frame bytes、no-network transport fake、history/fetch、replay/recovery与two-Shot chaining。

Official derivation contract：

- upstream repository固定为`Comfy-Org/workflow_templates`，commit固定为`0e0f4577453136eaa1c0e9d4b700e3e5ce5bb416`，path固定为`templates/video_minimax_h3_i2v.json`，raw JSON SHA-256固定为`313b029321a8be303e827dad471bff3022ca564c8bf8c6198a3e70b65c599671`，license记录为MIT；
- derivation清单必须记录UI/subgraph到deterministic API-format JSON的全部有意修改，包括删除UI-only notes、demo input asset和非必需subgraph/UI metadata；
- optional LoRA、remote refiner与cloud fallback默认关闭，同时保留官方native H3 conditioning、sampling、video/audio decode和MP4 output contract；
- exact terminal PNG只绑定到`MiniMaxH3ImageToVideo.first_frame`；`last_frame`只有在request与profile均显式要求时才出现，且不得把`ref2va`与`fl2va`混成同一个profile；
- upstream新版本不得自动覆盖sealed profile；upgrade必须重新review、记录derived diff、重新seal全部hash并重新验收。

`workflows/profiles/minimax_h3_fl2va.json`至少必须seal：

- upstream repository、commit、path、raw JSON hash与license；
- derived API workflow hash与binding hash；
- exact ComfyUI commit；
- `minimax_h3_fl2va_pruned_int8_convrot.safetensors`、`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`minimax_h3_video_vae_fp16.safetensors`、`minimax_h3_audio_vae_fp32.safetensors`四个model component hashes；
- required native node inventory，包括`MiniMaxH3ImageToVideo`及官方conditioning、sampling、video/audio decode与MP4 output path所需nodes；
- literal loopback endpoints；
- resolution、17k+5 frame-grid、duration、native-audio与output bounds。

Offline tests除既有adapter/replay/recovery assertions外，必须证明：

- pinned upstream provenance能够reopen，并验证repository/commit/path/raw hash/license与derived modification manifest；
- template、binding或profile任一hash tampering均fail closed；
- exact terminal PNG bytes进入`first_frame`，不是仅path/name相同；
- optional `last_frame`不会被adapter或template静默增加、删除或降级；
- transport/profile没有remote endpoint、proxy、refiner或cloud fallback；
- official upstream发生变化时不会绕过profile resealing或自动改变active production identity。

Implementation必须复用现有`VideoGenerationRequest`、`ContinuityReferenceBinding`、terminal evidence、Manifest 2.8与P5 continuity edge；不得新增local-only continuity schema、第二writer或第二resolver。`fl2va`是最小必需lane，`ref2va`是identity/reference增强lane。

任何local adapter都必须无remote fallback、默认不联网，并以Fake/sealed loopback tests证明`first_frame` exact bytes进入workflow binding。它必须seal ComfyUI commit、checkpoint/text encoder/VAE hashes、workflow/binding/profile hashes、registered nodes、FPS/duration limits和output capability。上述Local H3 surface已在本次明确授权下实现；`ref2va`或任何新的provider/profile仍需要独立implementation authorization。

### Lane B: MiniMax Cloud Hailuo 2.3

Target surface：

- `src/ai_video/production/minimax_hailuo.py`
- `tests/test_production_minimax_hailuo.py`

基于 refreshed official profile，新增 `MiniMax-Hailuo-2.3` I2V variant和 `first_frame_image` mapping。Tests 必须检查 exact model、image encoding/reference、duration/resolution coupling、sanitized failures、authorization/permit、submit-once 和 unsupported last-frame denial。不得因其他 Hailuo model 有 first/last-frame API 就把该能力外推到 2.3。

Offline verification：

```bash
pytest -q tests/test_production_minimax_hailuo.py tests/test_production_video.py
```

2026-08-20 live result：首个request证明Provider的`768P`输出为adaptive `1326x768`；其zero-network receipt migration不计canonical lifecycle。用户随后授权的新bounded adaptive request继续消费exact activated keyframe SHA-256 `5072a65b0e13a7fae2b809d3dc0afb24dc6980c75b0ce9342559b60801c158fc`作为`first_frame_image`，唯一一次POST生成task `432581080539416`与MP4 SHA-256 `90b4fc1842b4a74332ebcae7e20c1e0cc1cdd7166037702e4dd1b37d2ed0bdca`。输出为`1326x768@24fps`、141 frames、5.875s、MP4、no-audio；candidate activation、reopen、recovery、P5 closure与zero-effect replay全部canonical通过。Project-local `video-analysis`、black/freeze和7点抽帧检查通过，首帧SSIM为`0.941854`。

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

2026-08-20 live preflight result：exact model/capability与`generate_audio=false`保持sealed；按官方`23 CNY / million tokens`与仓库token公式计算2.484 CNY，并seal保守`3 CNY` preview upper bound。后续bugfix已实现sealed Ark Console `Active` materialization receipt与exact local-asset resolver，补齐可验证的identity import owner；但Shared keyframe仍没有真实Ark `asset-...`和confirmation evidence，因此authorization/permit未签发且POST为零。P8 Seedance plan新增的inline-Base64 synthetic/illustrated lane仍是未实现、未授权的独立后续task，只允许sealed且human-attested的明确非真人/非受保护角色或普通非角色图片；Alice photorealistic keyframe明确不符合该V1分类。因此本continuity lane的external materialization gate不能由该proposal、Hailuo success、临时第三方URL或猜测upload API替代。

### Execution Order for Cost Control

Provider-neutral continuity core保持唯一实现；Local H3、Hailuo与Seedance只在adapter/profile/capability mapping处分叉。切换lane不能只修改`model_id`，也不得复制terminal evidence、Manifest、P5或composition lifecycle。

为减少付费prompt/reference调试，后续execution order固定为：

1. 已完成Local H3 `fl2va` sealed workflow/profile与offline adapter tests。
2. 已在本次live-local授权下用exact Shot A terminal PNG生成Shot B本地draft，并验证terminal hash等于workflow消费的`first_frame` bytes。
3. 已使用`video-analysis`与无转场side-by-side完成technical inspection；blind human rubric、额外本地迭代与`ref2va`仍是独立后续scope。
4. 只有显式选中的Shot/continuity edge才进入Hailuo或Seedance paid lane；每次remote submit仍需要exact budget、egress与one-use permit。
5. Paid output重新执行自身activation/replay与subjective gate；Local H3成功不能外推为cloud model质量或payload acceptance。

本地GPU时间、电力、RAM/VRAM必须进入resource report，但不伪造remote budget receipt。不得实现自动“local失败后cloud fallback”或根据价格自动选Provider；lane promotion是显式production decision，并保留独立generation identity与provenance。

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

本 milestone 只有在用户以task-scoped request明确列出允许执行的lane/model/profile和调用边界后才能执行。当前任务已授权并完成Local H3 `fl2va` continuity proof；每个remote lane仍需要独立Budget Guard/Cloud Egress/bounded-call plan。不得把本地成功、旧cloud diagnostic或未列明的Provider当作其他lane授权。

每个 lane 的 live proof至少证明：

- exact provider/model/profile/capability snapshot；
- Shot N terminal evidence hash 等于 submit payload 消费的 first-frame bytes；
- exactly bounded submit/status/fetch，replay新增零调用；
- fetched MP4 measured validation、terminal evidence、candidate activation和 reopen/recovery；
- local lane的resource/runtime report或remote lane的cost/budget receipt完整；
- 不把一次 lane success 外推到其他 lane。

Local H3 accepted evidence位于`runs/h3-shot-continuity-live-20260819-v3/`：profile hash `456b59c7a907d4b07c7d951d63ec03cbd0fb5c64638dbc8dad870aca09e2b604`，loopback proof submit为2、remote call为0；Shot A terminal与Shot B `first_frame`共用SHA-256 `cb5bbc17ad361b4b8445657608e245c179446efb68a5976b4df09eb0ecbaf42c`，两个H.264/AAC MP4均为608x352、24fps、124 frames、5.167秒，Manifest最终revision为21，replay新增调用为零。一次较早diagnostic submit在fixture activation时fail closed且没有blind retry；它不计入accepted two-Shot proof。

## Milestone 10: Subjective Continuity Acceptance

在 live proof之后，为每条 continuity edge生成未加转场的 terminal/initial pair和最终序列。分别执行：

- local `video-analysis`：scene/character identity、camera direction、motion direction、lighting/color、entrance/exit和spatial relation逐项报告；
- blinded human review：使用预先冻结的 rubric，对同一维度评分并给出 blocking discontinuity；
- Provider/lane comparison：local、Hailuo 2.3、Seedance 2.0 Mini分别报告，不混合平均掩盖失败。

Subjective acceptance必须独立于 technical和live verdict。单一相似度、crossfade后观感或 prompt 文案一致均不足以通过。

## Milestone 11: Bounded Hybrid Continuity Evaluator V1

### Authorized Surface

- `src/ai_video/production/continuity_evaluator.py`：sealed local ONNX profile、RGB frame sampler、
  deterministic subject tracker 与 raw measurements；不产 verdict。
- `src/ai_video/production/review.py`：只扩展 backward-compatible raw measurement/profile identity。
- `src/ai_video/production/_lifecycle_schema.py`、`_state_commit_video*.py`、`video_artifact.py`、
  `video_generation.py`、reader/paths/models export：仅实现由唯一 committer 拥有的 evaluator evidence
  checkpoint、reopen 与 recovery；不得新增第二 writer。
- `tests/test_production_continuity_evaluator.py` 与最接近的 P8 lifecycle tests；Harness/docs 只按真实
  changed paths 同步。
- `pyproject.toml`：Option A 允许把现有 agent-memory extra 中的 pinned `numpy`/`onnxruntime` 范围
  提升为 Production base dependency；不得增加 OpenCV、SciPy、remote SDK 或其他 runtime dependency。

### TDD and Compatibility Order

1. RED：sealed profile/config/model hash进入 evidence identity；model bytes mismatch 在 session 创建前拒绝。
2. RED：fake deterministic detector/ReID outputs 覆盖 exact frame binding、方向反转、exit mismatch、
   same-track re-entry、低 confidence/coverage 与 ambiguous track `not_evaluated`。
3. RED：identity/axis/framing 无可信 backend 时保持 incomplete，并证明独立 human evidence仍可完成 P6。
4. RED：evaluator 完成后 candidate preparation 故障，recovery/retry不重复 sampler、ONNX evaluator或
   fallback side effect；tampered pointer/evidence fail closed。
5. GREEN：实现最小 cohesive adapter 与 Manifest-compatible checkpoint，保持历史 Manifest 2.8、旧
   `GeneratedShotContinuityEvidence` payload/hash、P3/P4/P5/Provider/activation contracts不变。
6. 运行 focused suites、native independent review、exact staged Harness与receipt self-verification，只
   提交 task-owned files。

### Offline Capability Boundary

本 milestone 不下载或捆绑模型。只有 fixture/fake-session tests 时，交付状态必须写成
`adapter and durable lifecycle accepted; live visual backend unavailable`。真实 detector/ReID assets
必须另行提供 license/source/exact SHA-256/size 与符合 profile 的 I/O contract，并经过 no-network local
smoke 后，才可升级为 live automatic evaluator capability；face-only detector不能外推为通用 continuity。

## Milestone 12: C4 Multi-Anchor Motion Continuity

本milestone由[Shot Continuity specification](../specs/2026-08-19-ai-video-shot-continuity.md)的`C4 Multi-Anchor Motion Continuity Contract`治理。它是新的ordered implementation lane，不回写C1/C2/C3历史语义，也不把v7失败take重新激活。

### Problem Boundary and Implementation Gate

- `single request owner`：`VideoGenerationRequest`与`ProviderNeutralVideoRequirement`继续拥有sealed provider-neutral input contract；不得在Seedance adapter中另造C4 request truth。
- `single selection owner`：`VideoGenerationResolver`继续独占exact capability selection；adapter compiler只做deterministic native projection。
- `single artifact/lifecycle owner`：Asset Registry与`ProductionStateCommitter`继续独占input identity、derived motion-tail evidence、durable write、activation与recovery。
- `single dependency/timing owners`：P5 Dependency Graph与`ResolvedTimeline`保持不变；motion-tail source range是generation evidence，不是第二timeline。
- `unchanged paid owners`：existing Paid Provider Gate、Cloud Egress、budget、durable intent、one-use permit与unknown-outcome recovery保持不变。
- `old C4 path removed`：C4不得继续使用first-frame-only Router projection、prompt identity substitute、three-static-image-only acceptance或separate capability union。
- `focused verification`：`python -m pytest`覆盖video requirement/request、Router、capability cardinality、Seedance materialization/payload、paid lifecycle、P5 closure、replay/recovery；最终以exact staged snapshot或exact commit range运行Harness。

Implementation开始前必须重新检查live agents、allowed paths、`git status`与exact target-file overlap，并获得新的runtime implementation authority。2026-08-22 docs lane开始时，`src/ai_video/production/seedance_asset.py`、`tests/test_production_seedance.py`、`.agent/harness/policy.yaml`、`tests/test_agent_harness.py`与`docs/agent-primary-contract-matrix.md`均存在其他session changes；本lane期间共享`main`又由外部session推进，前四个paths分别进入`cf5a357`与`5e2674a`，当前candidate-surface status recheck只剩`docs/agent-primary-contract-matrix.md`仍有uncommitted same-file overlap。由于这些external commits不出现在本thread live-agent tree中，future code lane不得把clean status解释为无人拥有；必须以当时fresh ownership evidence为准。未由用户决定仍在overlap的file ownership/顺序前不得写该file；其他完全不相交的target files不因此自动blocked。

### 12.1 RED — Freeze Rejection and Tamper Matrix

Target surface：

- `tests/test_production_video.py`
- `tests/test_production_video_requirement.py`
- `tests/test_production_shot_router.py`
- `tests/test_production_provider_neutral_adapters.py`
- `tests/test_production_seedance.py`

先运行并保存当前baseline，然后添加failing tests，证明当前validator拒绝`continuity_binding + independent reference`，current exact-terminal Router只输出`first_frame`，current Seedance Mini seal不能同时满足四个roles。RED matrix至少覆盖：

1. static C4缺terminal、identity或approved endpoint；motion C4另缺motion tail；
2. 任一semantic/native role重复、错role、错canonical order或额外undeclared binding；
3. terminal wrong source/candidate/Registry revision、terminal bytes/evidence tampered；
4. identity不是独立canonical Character asset、owner/revision/hash不匹配或由terminal/scene plate冒充；
5. endpoint缺human approval/feasibility receipt、wrong target Shot、hash/dimensions tampered或不可达；
6. motion tail不是accepted upstream artifact的精确尾段、range/frame count/hash/receipt tampered、未以terminal frame结束或来自另一个take；
7. capability只支持任意子集或多个capability并集时，Router/adapter/preview/submit call count均为零；
8. C1/C2/C3与legacy empty-C4 payload、request/resolved/capability fingerprints逐字节保持兼容。

Test fixtures必须显式冻结`open_state -> changes_here -> close_state`：terminal/motion tail提供open motion phase，canonical identity/red satchel/axis/screen direction进入must-hold，approved endpoint提供close pose/FOV/scale。v7 regression分别标记`F-ID-DRIFT`与`F-CAMERA-PATH`/`F-CONTINUITY`，不以prompt变长作为expected fix。

Focused RED command：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video.py \
  tests/test_production_video_requirement.py \
  tests/test_production_shot_router.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_seedance.py -q
```

### 12.2 GREEN — Provider-Neutral Request and Cardinality Contract

Target surface：

- `src/ai_video/production/_video_continuity.py`
- `src/ai_video/production/video_artifact.py`
- `src/ai_video/production/video_requirement.py`
- `src/ai_video/production/video_contracts.py`
- `src/ai_video/production/video.py`
- `src/ai_video/production/_video_capability_fingerprint.py`
- closest tests from 12.1

以最小strict models实现spec冻结的四个semantic anchors：`continuity_terminal -> first_frame`、`identity -> reference`、`approved_endpoint -> last_frame`与`continuity_motion_tail -> reference_video`。Motion-tail evidence必须绑定accepted source artifact、rational time range、inclusive frame range、exact extracted bytes与receipt；endpoint必须绑定feasibility receipt。所有anchors都必须绑定Registry revision、SHA-256、role、provenance与materialization receipt identity。

扩展`ProviderNeutralVideoRequirement`与`VideoGenerationRequest`时使用additive schema/version selection；C4 fields缺失时历史hash/reopen完全不变。C4 validator只接受exact static three-anchor shape或exact motion four-anchor shape，并把所选tier的全部anchor/evidence/materialization hashes纳入request、resolved、activation-scope与desired fingerprints。`input_artifact_ids`和P5 inputs必须包含所选tier的全部exact Registry assets/evidence，不得以prompt或provider URI代替。

`VideoBindingCardinalityConstraint`分别冻结static exact grammar（`first_frame=1`、`last_frame=1`、`reference=1`、`reference_video=0`、`reference_audio=0`、all-role total `=3`）与motion exact grammar（前三个仍各为1、`reference_video=1`、`reference_audio=0`、all-role total `=4`）。Constraint canonicalization/fingerprint仍保持legacy empty-constraint omission semantics；static pass不得被报告为motion pass。

### 12.3 GREEN — Exact Router Projection

Target surface：

- `src/ai_video/production/_video_requirement_routing.py`
- `src/ai_video/production/shot_router.py`
- `tests/test_production_shot_router.py`
- `tests/test_production_video_requirement.py`

扩展`requirement_bindings()`的exact pool与role mapping，使C4 provider-bound projection一一绑定terminal、canonical identity、approved endpoint与motion tail。Semantic slots必须保持spec固定身份；`VideoGenerationRequest.image_bindings`与`media_bindings`按现有唯一canonical order序列化，role/asset pair不得因排序分离。

`VideoGenerationResolver`只可选择一个满足完整mode、roles、media bounds与cardinality的variant。Missing/stale inputs、wrong target、selected capability subset或officially unproven mode必须返回typed capability/missing-input denial；不得尝试T2V、R2V、I2V或另一个Provider fallback。C1 exact-terminal behavior继续只投影`first_frame`，只有显式C4 requirement进入four-anchor projection。

### 12.4 GREEN/STOP — Capability Seal and Provider Projection

Target surface：

- `src/ai_video/production/seedance_capabilities.py`
- `src/ai_video/production/seedance_profile.py`
- `src/ai_video/production/seedance.py`
- `tests/test_production_seedance.py`
- governing Seedance spec/runtime baseline/contract matrix only after implementation truth changes

先取得dated formal API evidence，证明`doubao-seedance-2-0-mini-260615`在同一native request/mode中支持`first_frame + last_frame + reference_image + reference_video`，并记录exact request schema、limits与model identity。Adapter现有`reference_image`serialization、其他Seedance 2.0 model、2.5 capability、Skill或UI行为均不足以证明Mini mixed contract。

- 若formal evidence完整：新增独立C4 capability/profile version与fingerprint，声明full cardinality、media semantics、MIME/geometry/duration/output bounds；Provider-specific compiler只把verified provider-bound inputs投影到exact native payload，不重创作或删除bindings。
- 若formal evidence缺失或含糊：不得修改`default_seedance_capabilities()`现有Mini seal；添加fail-closed tests并把Seedance C4状态报告为`blocked before paid preview/POST`。不得伪造mixed capability或改选Provider。

任何profile/API evidence变化都必须重新seal capability fingerprint并验证injected profile不能扩大official matrix。

### 12.5 GREEN — Materialization, Cloud Egress, Preview and Permit Fingerprint

Target surface：

- `src/ai_video/production/seedance_asset.py`
- `src/ai_video/production/seedance.py`
- existing paid-provider preview/permit surfaces only where exact C4 binding requires
- `tests/test_production_seedance.py`
- closest paid-provider state/E2E tests

为terminal、identity、endpoint与motion tail分别验证exact Asset Registry ID/revision/SHA/MIME/size、provenance和provider materialization receipt。Motion tail materialization必须引用derived tail bytes，而不是整个source video、review derivative或filename。`SeedanceAssetReferenceResolver`只能为四个exact bindings返回receipt-backed active Ark identities；缺失、重复、confirmation evidence mismatch或local Registry ID冒充`asset://`必须fail closed。

Paid preview的egress items必须逐项包含prompt与四个anchor bytes identities；budget/authorization、Cloud Egress、durable submit intent和one-use permit fingerprint必须绑定同一C4 request、capability、materialization receipts与ordered egress list。任一值变化都需要新preview/authorization/permit；unknown outcome不得blind retry或remint。失败必须发生在permit consume与POST之前。

### 12.6 GREEN — Offline Payload, Materialization, Replay, Recovery and P5

Target surface：

- tests from 12.1 and 12.5
- `tests/test_production_paid_provider.py`
- `tests/test_production_paid_provider_state.py`
- `tests/test_production_paid_provider_e2e.py`
- `tests/test_production_video_state_recovery.py`
- `tests/test_production_generated_video_e2e.py`
- `tests/test_production_dependency.py`
- `tests/test_production_selective_rebuild.py`
- existing committer/dependency implementation only if RED evidence proves a gap

使用Fake transport和sealed local fixtures证明：

- supported C4 capability产生exact deterministic payload，四个bindings与materialized identities逐项匹配，offline tests不触网、不读取credential、不消费permit；
- missing/tampered/stale materialization、payload role/order drift、capability/profile fingerprint drift均在external effect前拒绝；
- exact replay不重复motion-tail extraction、materialization、preview、submit、poll、fetch、validation、activation或render；
- before-submit、accepted、known-no-effect、outcome-unknown、fetched、validated与activation crash points继续走existing explicit recovery，unknown不自动retry；
- terminal/identity/endpoint/tail任一变化只stale target generation与真实composition/render closure；unlinked Shots、voice、captions与unrelated assets保持fresh；
- static boundary evidence与motion boundary evidence分别seal、reopen并由P6 adjudication，不把SSIM或Provider result直接写成Final Acceptance。

Focused verification至少运行policy映射的`provider_neutral_video_requirement_tests`、`production_shot_router_tests`、`production_video_provider_tests`与task Architecture Gate；实际changed paths触发更多checks时以Harness inspection为准。

### 12.7 Exact Snapshot Harness and Checkpoint

完成implementation与focused tests后：

1. 重新检查live agents、exact target ownership和`git diff`；解决任何same-file conflict，保留unrelated dirty work。
2. 只用`git add <exact-task-files>`建立non-empty staged snapshot；不得stage其他session changes。
3. 运行Harness inspection，再对exact staged snapshot执行`make harness-verify`；若先形成task-only checkpoint，则用exact commit range执行`make harness-verify-range BASE_REF=<ref>`。
4. 用`make harness-receipt RECEIPT=<path>`验证scope、policy、artifact hashes与freshness，并创建task-only checkpoint commit；不得push/release。

Harness不运行Provider、media generation或paid smoke；passing receipt只能证明offline code/control-plane gates。

### 12.8 Native Independent Review

在code/tests与fresh Harness之后、任何live smoke之前，使用native named `reviewer`进行独立review。Reviewer必须检查：

- mixed binding是否真实由single capability表达，而非mode/capability union；
- validator/Router是否解决v7暴露的identity和camera-motion failure，而非只让tests通过；
- four-anchor tamper、materialization、egress、permit、replay/recovery与P5 closure是否fail closed；
- historical C1/C2/C3 hashes与unchanged owners是否保持；
- tests是否覆盖真实current rejection path和wrong-order/duplicate/tampered cases。

输出必须含`Verdict`、blocking issues、non-blocking concerns、file/test evidence与minimal follow-up。Parent直接验证重要claims并关闭blocking issues；reviewer不能授权live execution或改写solution。

### 12.9 Separately Authorized C4 Live Smoke

只有以下条件全部满足后才可开始：implementation checkpoint、all focused tests、formal complete capability evidence、fresh passing Harness、native reviewer无blocking issue、exact inputs/materialization ready、Creative Skill preflight complete，以及新的task-scoped paid authorization、fresh budget/egress decision和新的one-use permit。

Live smoke必须使用一个exact Provider/model/profile/capability、预先冻结的Shot open/close state与四个anchors；调用次数/预算必须bounded，不允许automatic retry、T2V/prompt/Provider fallback。先报告`C4_STATIC_BOUNDARY`，再以full-speed playback、upstream/downstream motion measurements与human/user visual review单独报告`C4_MOTION_BOUNDARY`。SSIM只作辅助；任何identity、axis、screen direction、subject scale/FOV、reachable displacement、teleport、gait phase、subject/camera velocity维度失败都保持C4 rejected/pending并禁止activation。

v7已经消费的authorization、permit、submit与fetched artifact全部不可复用；新live smoke不得自动激活candidate，也不得把Provider success或reviewer verdict当Final Acceptance。

## Documentation Closure

本次Local H3 implementation完成后同步更新runtime baseline、roadmap、primary contract matrix与AGENTS中的runtime truth，并清楚记录：

- provider-neutral contract已实现范围；
- 每个 provider lane的offline/live/quality状态；
- schema/layout是否保持不变；
- Harness receipt、local evidence与未授权 lane；
- rollback和known limitations。

原 P8 provider spec保持历史和当前 provider contract，不被重写成 continuity spec。

C4 implementation完成后再同步runtime baseline、contract matrix、Harness routing与Seedance provider docs；在此之前只能描述为`frozen target / implementation pending`。若formal Mini API evidence不能证明full mixed capability，documentation closure必须保留Seedance C4 pre-preview blocker，不得把fail-closed状态写成live-ready。

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

`C4_MULTI_ANCHOR_MOTION_CONTINUITY complete`另要求Milestone 12.1-12.8全部完成、selected Provider formal capability evidence完整，并在new authorization下分别通过static boundary与motion boundary live/subjective acceptance。仅完成three-static-anchor technical path时必须报告`C4 static boundary only`；没有exact motion tail或full-speed human acceptance时不得称motion continuity已解决。
