# AI-VIDEO Minimal Shot Continuity Proof Implementation Plan

## Objective

实现并验证 [Minimal Shot Continuity Proof specification](../specs/2026-08-19-ai-video-minimal-shot-continuity-proof.md) 中的 `C2_HARD_CUT_KEYFRAME_I2V`：P7 local image generation真实消费canonical character reference与Shot 1 activated terminal evidence，生成独立构图的Shot 2 keyframe；随后既有Local H3 `fl2va`以该keyframe为exact first frame生成Shot 2视频。

本计划不实现Shot Router，不调用任何cloud/remote/paid Provider，不修改CLI，不新增第二writer、timeline、renderer或dependency resolver。

2026-08-20 status note：后续用户另行授权的cloud comparison不属于本计划执行authority，但复用了本计划的Alice terminal与activated P7 hard-cut keyframe。Hailuo 2.3 lane已one-submit succeeded/fetched/measured并通过visual review with minor concerns，但canonical activation因duplicate external-effect receipt migration被拒绝；Seedance在current price/Ark asset materialization gate前fail closed并保持零submit。Local H3 Shot 2仍未执行，因此本计划Definition of Done与Router gate均未达成。

## Current and Target Behavior

当前行为：

- `C1_CONTINUATION_I2V`已能把Shot N terminal PNG直接绑定为Shot N+1 video first frame，并具备Manifest 2.8 lifecycle、recovery、replay和P5 continuity edge。
- `ImageReferenceBinding.role`只允许`character`、`scene`、`style`并要求creative ownership；`ImageGenerationRequest`要求`character + scene`。
- P7.1 local image profile最多接收两个references。
- 尚不能表达或验证“P7 keyframe generation消费upstream terminal，再由P8 video消费derived keyframe”的hard-cut lineage。

目标行为：

- ordinary P7 path继续要求`character + scene`，完全兼容。
- hard-cut P7 path允许且只允许`character + continuity_terminal`。
- 新的strict terminal reference binding绑定exact activated source Shot/candidate/generation/terminal evidence与target Shot/constraints，不伪造creative ownership。
- generated keyframe provenance与P5 graph保留source terminal lineage。
- Shot 2 video request精确绑定derived keyframe，并sealterminal-to-keyframe lineage；不得谎称H3直接消费terminal。

## Problem Boundary

- Single durable owner：`ProductionStateCommitter`。
- Old path retained：现有ordinary P7 image generation、C1 terminal-first-frame video path与all provider adapters保持可用。
- New responsibility：provider-neutral hard-cut keyframe reference/binding与typed dependency lineage。
- Unchanged contracts：`ResolvedTimeline`、HyperFrames、P4 audio/captions/final mux、Legacy CLI/layout、default no-network、generated-MP4 compatibility。
- Focused verification：P7 request/candidate/state、P8 request/local state、P5 dependency/selective rebuild、project reopen/recovery。

## Scope-Expansion Gate

实现前默认假设无需Manifest/Registry schema version、公共artifact layout、CLI或第三个image reference。若RED spike证明任一项不可避免，停止实现并报告exact blocker；不得在本计划内自行扩展。

允许的最小contract extension：

- strict provider-neutral `continuity_terminal` image reference/binding；
- strict hard-cut lineage binding in video request/evidence；
- existing P5 graph中的typed edge/contribution；
- corresponding public imports only if existing production API pattern requires。

## Implementation Entry Gate

Spec/plan本身不授予implementation authority。当前用户已明确要求“执行plan”并选择“升级Hard-cut”，因此本任务可以在docs checkpoint后进入C2 technical implementation与offline verification；该授权不包含GPU live generation、Router runtime、remote Provider、schema/layout/CLI expansion或付费调用。

## Milestone 1: RED — Freeze Hard-Cut Image Request Contract

### Target Files

- `tests/test_production_image.py`
- `tests/test_production_comfy_image.py`
- `src/ai_video/production/image.py`
- `src/ai_video/production/comfy_image.py`
- new additive hard-cut profile under `workflows/profiles/`
- corresponding sealed P7.1 test profile fixtures

### RED Contract

先添加failing tests：

1. ordinary `character + scene` request保持合法，fingerprint不变。
2. hard-cut `character + continuity_terminal` request合法且fingerprint覆盖terminal evidence与constraints。
3. `continuity_terminal`只接受exact activated source terminal；wrong source Shot/candidate/generation/Registry revision、tampered/unreadable PNG、wrong dimensions与symlink escape拒绝。
4. hard-cut request缺character或terminal、混入ordinary scene、duplicate roles或超过two-reference bound拒绝。
5. unsupported local profile在preview/submit前返回typed capability denial，transport call count为零。
6. rendered local image workflow第二reference exact bytes hash等于terminal PNG hash。

### GREEN Work

- 在P7 provider-neutral model中增加strict `ContinuityTerminalImageReferenceBinding`，与既有`ImageReferenceBinding`组成discriminated union；不修改ordinary reference的creative ownership语义。
- 将request validation改为两个明确的reference shape，不使用宽松“任意两张图”。
- hard-cut request使用新的fingerprint schema tag；ordinary request继续产生与当前完全相同的v1 fingerprint。
- 扩展local image profile model的role allowlist和binding validation，但保持`max_references == 2`；新增profile file与content hash，不原地改写accepted Qwen/FLUX profiles。
- 不把terminal转换成prompt-only metadata；adapter必须读取sealed exact bytes。

### Verification

```bash
pytest -q tests/test_production_image.py tests/test_production_comfy_image.py
```

## Milestone 2: RED — Seal Keyframe Artifact and Durable Lifecycle

### Target Files

- `tests/test_production_image_e2e.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `src/ai_video/production/image.py`
- `src/ai_video/production/_state_commit_image_intent.py`
- `src/ai_video/production/_state_commit_image_candidate.py`
- `src/ai_video/production/_state_commit_image_activation.py`
- `src/ai_video/production/_image_project_reader.py`
- `src/ai_video/production/state_commit.py`

### RED Contract

- generated keyframe `AssetRecord.input_artifact_ids`只包含graph-addressable canonical character asset/artifact ID与terminal asset ID；terminal evidence/extraction/request/provenance hashes进入sealed evidence contributions，不产生dangling graph input。
- prepared candidate只改变target Shot visual projection并append一个image asset；不能覆盖source Shot或unrelated Registry entries。
- reopen验证request、reference bytes、keyframe bytes和provenance。
- before-submit、after-submit-unknown、fetched/prepared、activation commit point前后均有recovery tests。
- exact replay的image submit/fetch/candidate preparation/activation增量为零。

### GREEN Work

复用P7现有intent/candidate/activation transaction，不增加writer。只有在现有fields无法无歧义表达terminal lineage时新增strict evidence field；若需要schema bump则触发Scope-Expansion Gate。

### Verification

```bash
pytest -q \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py
```

## Milestone 3: RED — Bind Derived Keyframe to Video Request

### Target Files

- `tests/test_production_video.py`
- `tests/test_production_comfy_video.py`
- `tests/test_production_local_video_state.py`
- `src/ai_video/production/video.py`
- `src/ai_video/production/video_contracts.py`
- `src/ai_video/production/comfy_video.py`

### RED Contract

1. hard-cut video request必须是`image_to_video`，first-frame绑定activated keyframe。
2. lineage binding同时sealupstream terminal、P7 request/output、target Shot与continuity constraints。
3. keyframe provenance不指向terminal、target mismatch、keyframe tampered或request hash mismatch时fail closed。
4. rendered H3 workflow first-frame bytes hash等于keyframe hash。
5. C1 existing terminal-first-frame request继续合法；C1与C2 binding不得混淆。
6. capability denial、non-loopback endpoint与profile tampering的submit count为零。
7. 当hard-cut field缺失时，历史T2V、ordinary I2V与C1 serialized requests/receipts可原样reopen，`request_input_hash`、activation-scope fingerprint、desired request fingerprint与`resolved_generation_hash`逐字节不变。

### GREEN Work

增加最小`HardCutKeyframeBinding`或等价strict model。它只描述真实lineage，不复制P7 evidence、不改变Provider-specific payload；新field采用compatible omission与request schema selection，缺失时完全复用历史hash payload。`ComfyUIVideoProvider`继续只消费first-frame image；lineage validation在external effect前完成。

### Verification

```bash
pytest -q \
  tests/test_production_video.py \
  tests/test_production_comfy_video.py \
  tests/test_production_local_video_state.py
```

## Milestone 4: RED — Add Precise P5 Closure

### Target Files

- `tests/test_production_dependency.py`
- `tests/test_production_selective_rebuild.py`
- `tests/test_production_generated_video_e2e.py`
- `src/ai_video/production/dependency.py`
- `src/ai_video/production/video_dependency.py`

### RED Contract

构造至少三个Shot，显式证明：

- source video/terminal变化 -> target keyframe -> target video -> existing composition/render closure stale；
- character reference变化产生相同closure；
- keyframe request/output变化不stale source Shot；
- target video-only motion/output/profile变化不stale keyframe；
- unlinked N+2、voice、captions、BGM与unrelated assets保持fresh；
- N+2只有存在explicit typed edge才transitive stale；
- exact replay无execution unit或lifecycle advance。

### GREEN Work

优先复用Registry asset `input_artifact_ids`与existing asset edges；只有现有graph无法区分terminal-to-keyframe语义时增加typed edge/contribution。不得用Shot order推导edge，不得在P5保存mutable lifecycle或timeline。

### Verification

```bash
pytest -q \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_generated_video_e2e.py
```

## Milestone 5: Offline End-to-End and Regression Gate

### Target Files

- focused production tests touched by prior milestones
- `tests/test_production_project.py`
- `tests/test_production_registry.py`
- `tests/test_production_models.py`
- `tests/test_production_composition.py`
- `tests/test_production_hyperframes.py`

### Work

用Fake/local transport fixture完成terminal -> P7 keyframe -> H3 video -> activation/reopen -> P5 -> composition的offline闭环。验证P3/P4、Static Image、Legacy isolation、default no-network与old snapshots不回归。

### Verification

```bash
pytest -q \
  tests/test_production_image.py \
  tests/test_production_comfy_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_video.py \
  tests/test_production_comfy_video.py \
  tests/test_production_local_video_state.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py
```

## Milestone 6: Technical Acceptance and Stable Checkpoint

检查final diff与old-path compatibility；使用native named `reviewer`执行independent review并关闭blocking issues。精确stage task files，运行fresh staged Harness，校验receipt后创建task-only checkpoint commit。

```bash
git add <exact-task-files>
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
git commit -m "feat: add hard-cut shot continuity"
```

不得push或release。

## Milestone 7: Separately Bounded Local Live Proof

只有在technical checkpoint和新的live authorization后执行：

- fixture固定为Alice进入明亮咖啡厅、触碰椅背，再hard cut到拉椅坐下；
- 复用exact activated Shot 1时，最多一次P7 keyframe submit和一次H3 Shot 2 submit；若需重新生成Shot 1，必须另行列明并授权；
- 禁止remote endpoints、cloud Provider与automatic retry；
- 保存request/workflow/component hashes、terminal/keyframe/MP4 metadata、resource report、activation/reopen与zero-call replay evidence；
- local `video-analysis`与blinded human review分别评分。

若任何subjective blocking dimension低于4，C2保持pending。失败不得自动切换Hailuo、Seedance或新增第三reference。

## Definition of Done

只有technical、local live与subjective三层分别通过，且P5/recovery/replay证据完整，才能称C2最小闭环完成。Technical implementation完成但尚未live时必须报告`technical acceptance only`；Router implementation仍保持blocked。

## Rollback

回滚删除hard-cut-onlymodels、validation和typed edge，恢复ordinary P7与C1 paths。历史C1 evidence、P8 providers、Manifest 2.8、P5、composition、Static Image和Legacy runtime不得受影响。
