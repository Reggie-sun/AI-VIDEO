# AI-VIDEO Shot Router Implementation Plan

## Objective

实现 [Shot Router specification](../specs/2026-08-19-ai-video-shot-router.md) 对四档 Shot continuity contract 的消费：`ShotVisualResolver`产生authoring proposal，`VideoGenerationResolver`为已激活generated-video/hybrid Shot选择provider-neutral generation mode、required bindings与capability requirements；`exact_terminal`、`reference`、`semantic`、`none`具有互斥的pixel/state输入规则。Provider routing是正交维度，可以选择不同的exact Provider/profile，但不得改写或降级Shot continuity mode。

本计划不自动选择或fallback Provider，不调用network，不读取secret，不mint permit，不提交generation，不增加第二份durable `visual_strategy` truth。

## Entry Gate

开始任何Router runtime edit前必须确认：

1. C2 technical lineage已存在，但两轮representative subjective review未通过；
2. 用户明确选择诚实降级 Router，并要求继续 implementation；
3. C1 `h3-minimal-shot-continuity-proof-20260819-v1` 证明exact terminal直接进入Shot 2可得到连续动作，但不证明C2 derived-keyframe主观质量；
4. 当前task在用户授权的dedicated worktree中执行，无target-file ownership冲突；
5. no schema/layout/CLI/P5/state-writer mutation assumption仍成立。

`hard_cut`不属于continuity mode。既有C2 derived-keyframe主观质量失败仍不得被描述为quality accepted；真正的`reference` routing只有exact R2V capability满足terminal+canonical reference roles时才能选择。

## Problem Boundary

- Canonical authoring owner：activated `Shot` revision。
- Durable writer：`ProductionStateCommitter`。
- Generation lifecycle：existing `VideoGenerationRequest`与P8 state modules。
- Dependency owner：existing P5 graph/resolver。
- Timing/render owners：`ResolvedTimeline`与HyperFrames。
- Provider selection：Router core之外的explicit production policy给出exact provider/profile；Registry只做exact lookup。

Router必须可整体删除并恢复caller显式选择行为。

## Proposed Module Surface

优先新增独立cohesive module，避免继续扩大`video.py`：

- `src/ai_video/production/shot_router.py`
- `tests/test_production_shot_router.py`
- `src/ai_video/production/__init__.py`仅添加approved public imports

除非RED integration test证明不可避免，不修改models schema、Manifest、Registry、artifact layout或CLI。

## Milestone 1: RED — Freeze Pure Router Models and Hashes

### Tests

在`tests/test_production_shot_router.py`先定义failing tests：

- strict input绑定exact Shot/Storyboard/Character Bible/Scene/reference/terminal/capability/policy identities；
- `ShotVisualRoutingProposal`只有proposed/blocked outcomes，不可被request/P5/render直接消费；
- `VideoGenerationRoutingDecision`包含selected mode、ordered binding roles、exact inputs、capability/output requirements与stable reason codes；
- `semantic_routing_hash`只覆盖生成语义；`audit_decision_hash`额外覆盖policy与rationale；
- reference/semantic state hash必须先以canonical token物化进activated Shot的既有`continuity_constraints`；state变化由target Shot hash进入现有request/P5 truth，不建立第二份durable state；
- policy-only/rationale/order noise只改变audit hash或完全不变，不改变semantic hash；
- provider registration order与dict order不影响结果。

### Implementation

在`shot_router.py`实现strict immutable models和canonical hashing。reason codes使用closed enum，不让free text决定replay/invalidation。

### Verification

```bash
pytest -q tests/test_production_shot_router.py
```

## Milestone 2: RED — Implement Deterministic Visual Strategy Rules

### Tests

稳定以下priority matrix；continuity mode优先于没有continuity证明的既有素材复用：

1. approved existing clip -> `existing_video`。
2. no visible motion -> `static_image`。
3. transform/parallax only -> `image_motion`。
4. graphic/text animation -> `motion_graphics`。
5. `exact_terminal` -> generated video proposal with terminal-first-frame requirement。
6. `reference` -> terminal+canonical refs+semantic state as references，terminal不得成为first frame。
7. `semantic` -> typed state required，terminal必须排除。
8. `none` -> 不消费terminal/state；important character without visual anchors仍blocked，不得T2V。
9. identity-free free motion -> `generated_video + text_to_video`。
10. hero/edit/repair paths在第一阶段一律以`HERO_SHOT_REQUIRES_HYBRID_OR_V2V`阻断；未来只有在独立slice提供exact source-media binding与对应generation contract后才可选择hybrid/video edit，且不能作为continuity failure fallback。

### Implementation

`ShotVisualResolver`保持no-I/O pure function，只输出proposal。它不得创建Shot revision、写Manifest或选择Provider。

### Verification

```bash
pytest -q tests/test_production_shot_router.py
```

## Milestone 3: RED — Implement Video Generation Resolution

### Tests

- resolver只接受已经激活且strategy为generated-video/hybrid的Shot。
- `exact_terminal`选择I2V + exact terminal first-frame。
- `reference`选择R2V，terminal与canonical refs全部使用reference role，不得复制构图。
- `semantic`只seal typed continuity state并排除terminal pixels；`none`排除所有continuity输入。
- canonical references且exact profile支持时可选择R2V；不支持则blocked，不得fallback。
- reference bindings复用现有`VideoGenerationRequest` canonical order；等价caller tuple换序必须收敛到相同ordered inputs与semantic hash。
- T2V只适用于无重要identity、无continuity edge的free generation。
- selected exact provider/profile capability不满足required roles时blocked；不得查找下一个Provider。
- local resource、remote authorization、budget denial均为typed blocked result且无external effect。

### Implementation

`VideoGenerationResolver`读取external production policy预选的一个exact provider/profile capability snapshot。它输出provider-neutral requirements并能构造现有`VideoGenerationRequest`，但不调用Registry/Provider。

### Verification

```bash
pytest -q tests/test_production_shot_router.py tests/test_production_video.py
```

## Milestone 4: Preserve Single Writer Boundary

### Target Files

- `tests/test_production_shot_router.py`
- existing state/dependency modules remain unchanged

### Tests

- proposal只携带exact target identity、建议与audit hash，不写入任何state。
- 第一阶段不提供proposal materialization API；caller仍需显式authoring，只有既有`ProductionStateCommitter`可激活revision。
- Router module不得被P5/request/composition直接作为durable truth消费。

### Stop Gate

proposal materialization、durable Router receipt、Manifest/Registry schema或新的committer API全部留待独立scope expansion；不得给Router另建state writer或receipt store。

### Verification

```bash
pytest -q tests/test_production_shot_router.py tests/test_production_state_commit.py tests/test_production_state_recovery.py
```

## Milestone 5: RED — Preserve P5 Precision and Exact Replay

### Tests

- policy/audit-only变化不stale任何generation node。
- activated Shot semantic strategy变化只stale该Shot及真实downstream closure。
- mode/reference/terminal/keyframe/capability/output identity变化精确改变generation desired fingerprint。
- one Shot reroute不blanket stale episode中later Shots。
- exact decision/request replay不重复Provider、activation或render。
- P5不保存Router mutable state或derive timeline。

### Implementation

P5只消费activated Shot和sealed request已有semantic projection。只有RED test证明现有projection缺字段时做最小补充；Router policy/audit hash不得进入desired fingerprint。

### Verification

```bash
pytest -q \
  tests/test_production_shot_router.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py
```

## Milestone 6: Integration, Review, and Harness

构造representative inputs，覆盖static/image-motion/motion-graphics、四档continuity、I2V/R2V/T2V/existing/hybrid/blocked lanes，并证明C2 derived-keyframe主观失败没有被误写为reference quality acceptance。至少增加两套互不复用Character/Scene reference hashes、Shot intent/prompt和continuity state的variation cases，证明request保留各自exact prompt/reference set且hash随输入变化；不得用同一fixture的重复replay声称泛化。所有固定主角continuity Shot都不得路由到裸T2V，remote path未授权时不得触发secret、Budget Guard或network。

运行：

```bash
pytest -q \
  tests/test_production_shot_router.py \
  tests/test_production_video.py \
  tests/test_production_image.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py
```

使用native named `reviewer`检查single-truth、hash semantics、fallback denial、P5 precision与old-path compatibility。关闭blocking issues后精确stage、运行fresh Harness、校验receipt并创建task-only checkpoint commit：

```bash
git add <exact-task-files>
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
git commit -m "feat: add provider-neutral shot routing"
```

不得push/release。

## Acceptance

Technical acceptance要求：

- deterministic matrix与stable reason codes有executable tests；
- authoring proposal不成为second truth；
- 第一阶段没有proposal materialization或第二writer；
- 四档continuity均有typed executable contract；`exact_terminal`复制terminal到first frame，`reference`只作reference，`semantic`与`none`均不消费terminal pixels；
- 至少两套不同Character/Scene references、Shot prompt与continuity state通过同一contract；bindings、request prompt与request hash必须反映各自输入，而不是固定fixture；
- capability/resource/authorization denial全部fail closed；
- semantic/audit hash分离且P5 invalidation精确；
- no-network integration与fresh Harness通过。

Router technical acceptance不证明任何Provider live质量。Local H3、Hailuo、Seedance的live/quality evidence继续独立，且任何remote submit仍需新的task-scoped authorization。

## Rollback

删除`shot_router.py`、public imports和Router-only tests/integration seam，恢复显式authoring/caller selection。已由committer合法激活的Shot revisions保留；P7/P8、C1/C2 evidence、P5、P3/P4、Static Image与Legacy runtime不受影响。
