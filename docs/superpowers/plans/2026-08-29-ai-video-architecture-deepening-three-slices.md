# AI-VIDEO Architecture Deepening Plan: Retrieval, Video Lifecycle, And Requirement Invariants

## Status

Proposed。本 Plan 覆盖三个相互独立的 architecture slice：

1. 收敛 Agent Memory 双 retrieval path。
2. 深化 `VideoGenerationService` 的 local/remote lifecycle choreography。
3. 恢复 provider-neutral requirement invariants 的 locality。

本轮只固定后续 implementation contract，不修改 Product Runtime、不调用 Provider、不生成媒体、
不写 Production state，也不把历史 plan、RAG hit 或 test pass 外推为 runtime completion。

这三项不是同一个 refactor，也没有实现依赖。推荐执行顺序为 **Slice A → Slice C → Slice B**：
先消除低风险重复 owner，再收敛 pure in-process invariants，最后处理影响 permit、replay、activation
与 recovery 语义的 lifecycle interface。每个 Slice 必须使用独立 checkpoint、review、Harness receipt
和 rollback unit；任一 Slice 失败不得阻塞或污染其他 Slice。

## Goal

用三个更窄的 interface 隐藏三个目前泄漏给 caller/test 的 implementation concern，同时保持现有
canonical owners 与外部契约：

```text
Agent Memory callers
  -> canonical project retrieval + compatibility adapter
  -> one deep retrieval implementation

Production callers
  -> lane-bound, one-action lifecycle interface
  -> local / paid lane adapters
  -> ProductionStateCommitter remains the only durable writer

Planner / requirement / Provider adapters
  -> one provider-neutral invariant interface
  -> H3 owns only H3 expressibility and grammar
```

成功标准不是减少文件或方法数量本身，而是通过 deletion test：删除新的 deep implementation 后，
其复杂度会重新散回多个 callers；删除 compatibility adapter 时，只失去兼容入口，不会失去第二套
业务规则。

## Severity And Priority

| Slice | Current severity | Change risk | Why now |
| --- | --- | --- | --- |
| A. Agent Memory retrieval | Medium architecture debt；没有当前 data-loss/Production incident 证据 | Medium | 两条入口重复 scope、lock、manifest、query、run merge 与 release choreography，ranking/freshness change 需双处推理 |
| C. Requirement invariants | Medium-high correctness risk；没有已证实 regression | High | model、free validators 与 H3 adapter 形成 hidden cyclic seam，并由 adapter 重判 neutral validity |
| B. Video lifecycle | Medium architecture debt；没有已证实 Provider incident | Very high | caller 重复 local/remote dispatch，但重构会接触 paid permit、unknown outcome、exact replay、candidate activation 与 recovery contract |

因此这是需要治理的 substantive architecture debt，但不是要求 emergency rewrite 的现行故障。尤其 Slice B
必须以 behavior-preserving migration 处理，不能因 interface 变浅就一次性重写 state machine。

## Problem Boundary

### Slice A: Dual Retrieval Ownership

`src/ai_video/agent_memory/retrieval.py` 当前同时存在：

- `retrieve_project()`：canonical per-corpus shard interface，支持 `RetrievalResult`、per-shard freshness
  与显式 `allow_stale` last-good evidence。
- `search()` → `_search_unlocked()`：公开导出的 strict shared-leaf compatibility interface。
- `_query_leaf()` 与 `_search_runs()`：两套近似 collection query wrapper。
- `_search_collection()`：已经共享的 ranking/admission implementation。

CLI 只调用 `retrieve_project()`；repository 内没有 non-test `search()` caller，但 `search()` 仍由
`ai_video.agent_memory.__init__` 导出，且 current durable record 明确保留 strict compatibility。
问题不是两种 layout 本身，而是两种 layout 各自拥有一套 query lifecycle。

### Slice B: Caller-Owned Lane Choreography

`VideoGenerationService` 已正确隐藏 substantial permit/state choreography，但 public surface 仍暴露成：

- remote：`submit_once()`、`refresh_once()`、`fetch_once()`；
- local：`submit_local_once()`、`refresh_local_once()`、`fetch_local_once()`；
- staged post-fetch：`validate_once()`、`activate_once()`；
- legacy compound compatibility：`fetch_and_activate()`。

`EcommerceShotFacade` 在 submit/poll/fetch 三次重复 lane dispatch；M0/source operators 也重复读取
`resume_next_action()` 后构造 service 并选择 local method。caller 因而需要知道 Provider lane 和
Manifest phase 两层 implementation detail。

### Slice C: Neutral Invariants Across A Cyclic Seam

`_video_intent_validation.py` runtime-imports `video_requirement.py` 的 concrete model types；
`video_requirement.py` 又在 Pydantic validators 中 local-import validation functions。与此同时
`_h3_prompt.py` 再次调用 neutral validators 并过滤 compatibility diagnostics。结果是：

- neutral model validity、historical compatibility 与 H3 expressibility 不能在一个 interface 上解释；
- planner、model、quality gate、H3 adapter 与 tests 直接依赖 granular helper names；
- bypass/tamper fail-closed coverage容易退化成针对 implementation helper 的 tests。

问题不是 invariant implementation 太浅，而是 its interface 泄漏且 dependency direction 不清晰。

## Scope

### In Scope

- 在现有 modules 内建立 single owner，并删除或隔离 duplicate old paths。
- 用 characterization/RED tests 固定 current behavior，再迁移 callers/tests。
- 保持 current public behavior；public compatibility removal 只作为单独 decision gate。
- 同步 `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md` 与直接相关 durable record，
  但只在相应 implementation 已验证后描述 current behavior。
- 为每个 Slice 单独运行 focused tests、Architecture Gate、exact staged Harness 与 independent review。

### Out Of Scope

- Provider Console 或其他第四个 architecture candidate。
- Agent Memory index/schema、embedding model、ranking policy、corpus authority 或 refresh/build lifecycle变化。
- 新 Product subsystem、new database、new public CLI、schema/Manifest/artifact-layout migration。
- 新 Provider selection、remote fallback、automatic retry/recovery/activation 或 second lifecycle writer。
- 改变 Router、`compile_provider_video_request()`、唯一 `VideoGenerationRequest` compiler owner。
- H3 prompt redesign、Provider capability redesign、live/paid/local media execution或quality acceptance。
- 仅为减少行数而拆散 correctness-critical transaction choreography。

## Global Invariants

- `ProductionStateCommitter` 始终是唯一 v2 durable write、activation 与 recovery owner。
- 一次 canonical call 最多执行一个 Provider effect；允许为该 effect 紧邻完成必要的 durable intent、permit
  与 outcome receipt writes，但不得自动跨 submit → poll → fetch → validate → activate actions串联。
- exact replay 不得重复 Provider、renderer、analyzer、permit mint 或 Manifest write。
- unknown outcome 必须 fail closed；不得 blind retry、remint permit 或猜测 mixed state。
- local stack-bound submit 的 pre-submit guard 必须继续在 preview 前与 committer intent lock 内各验证一次。
- paid submit 继续要求 exact preview、budget reservation、cloud egress、actor authorization、durable intent
  与 one-use permit。
- Agent Memory retrieval 继续 read-only、no-network、no build/repair/queue-on-query，并保持 advisory authority。
- provider-neutral hashes、serialization 与 historical `/1`–`/4` reopen 必须 bit-for-bit 不变。
- Shot Router 仍唯一选择 Provider/profile/capability；adapter 只做 deterministic expression，不得 rewrite/fallback。
- `_h3_prompt.py` 只拥有 H3 native expressibility 与 three-field grammar，不拥有 neutral validity。
- Tests 必须以 module interface 的 observable behavior 为主；只为算法或 pure diagnostic 保留必要的
  implementation-level tests。

## Slice A — Converge Agent Memory Retrieval

### Target Architecture

保留两个真实 layout adapter，但只保留一个 query lifecycle implementation：

```text
retrieve_project()                     search()
canonical sharded adapter              strict shared-leaf compatibility adapter
          \                            /
           -> private deep retrieval implementation
              - one query/null embedding pair
              - quota allocation
              - validated collection query
              - explicit run-summary merge
              - freshness projection
              - stable ranking/truncation
              - exact client release
```

`retrieve_project()` + `RetrievalResult` 是 canonical project interface。`search()` 在本 Slice 保留 exact
signature、return type、export、scope values、strict/no-stale semantics、run opt-in 与 root-free freshness
limitation，只变成 thin compatibility adapter。

layout-specific validation 是真实 variation，继续由 adapter 拥有：canonical shards 可以显式返回 tagged
stale last-good；compatibility leaf 继续 strict，且 root-free caller 只能证明 materialized identity/physical
completeness。共同的 embedding、query、merge、ranking 与 release 不得再重复。

### Single Owner And Old Path

- Single owner：`retrieval.py` 内一个 private deep retrieval implementation。
- Canonical interface：`retrieve_project()`。
- Compatibility interface：`search()`，只做 legacy argument/layout normalization。
- Retire：`_search_unlocked()`、`_search_runs()` 及因此 orphan 的 imports/branches。
- Must remain：`_search_collection()` 的 dense/BM25 admission semantics；允许重命名但不得改变行为。
- No fallback：删除 old path 后不得保留隐藏开关或异常时回退到 duplicate implementation。

### Owned Files

Required：

- `src/ai_video/agent_memory/retrieval.py`
- `tests/test_agent_memory.py`
- `docs/record_for_agent/2026-08-21-agent-memory-rag-scope-and-retrieval.md`

Expected unchanged unless evidence proves otherwise：

- `scripts/agent_memory.py`（已经调用 canonical interface）
- `src/ai_video/agent_memory/__init__.py`（本 Slice 保留两个 exports）
- `index.py`、`layout.py`、`manifest.py`、`corpus.py`、`config.py`

### Milestones

1. **Freeze public parity with RED/characterization tests**
   - 对等 materialization 下比较两个 public interfaces 的 ordered `Hit` fields。
   - 固定 intentional differences：strict vs `allow_stale`、root-free limitation、`scope="all"` caller-supplied
     corpora、explicit run-summary opt-in、missing/corrupt index errors。
   - 通过两个 public interfaces 的 observable parity固定共同 choreography；tests不绑定 private symbol名称。

2. **Introduce one deep implementation**
   - 每次 request 只计算一组 query/null embeddings。
   - 集中 quota、per-collection query、freshness metadata、run merge、sort/truncate。
   - validation → query 全程保持 shared activation lock；每个 unique Chroma path 只 release 一次。

3. **Retire duplicate implementation**
   - 删除 `_search_unlocked()` 与 `_search_runs()`。
   - 清理 only-task-owned orphan imports。
   - 不创建第二个 module、index format 或 public interface。

4. **Move tests to stable interfaces**
   - project retrieval、freshness、quota、metadata、merge 与 run summaries 主要通过 `retrieve_project()`。
   - `search()` 只保留 compatibility-contract tests。
   - `_search_collection()` 只保留 ranking/calibration pure tests。
   - 用 Architecture Gate / exact `rg` retirement check防止 `_search_unlocked` / `_search_runs` 回归，
     不让 behavior tests依赖 private implementation名称。

5. **Update current documentation after executable proof**
   - durable record 明确 `retrieve_project()` canonical、`search()` compatibility、single internal owner。
   - authority、stale、maintenance、no-network/no-build/no-Production-state 边界不变。

### Acceptance Criteria

- `_search_unlocked` 与 `_search_runs` 不存在。
- CLI 仍只使用 `retrieve_project()`。
- `search()` exact public contract不变；external consumer 未知，因此不在本 Slice 删除 export。
- Top-30 candidate budget、Top-8 default、scope quota、lane-aware admission、authority/status/classification
  metadata、stable ordering 与 run-summary merge 不变。
- stale-last-good 不能掩盖 identity/physical corruption。
- `retrieval.py` 不增长；duplicate deletion 后 SHOULD 回到 800 lines guidance 附近或以下。

### Focused Verification

```bash
python -m pytest -p no:cacheprovider tests/test_agent_memory.py -q
python -m scripts.architecture_gate check
git diff --check
python -m scripts.agent_harness inspect --staged
python -m scripts.agent_harness verify --staged
python -m scripts.agent_harness verify-receipt <receipt-path>
```

### Compatibility Gate And Rollback

删除 `search()` 需要独立 public-contract approval，并先完成 external/package consumer inventory、
`build_index()`/shared-leaf migration、`__all__`/release notes/migration guidance 更新。本 Slice 的 rollback
unit 是一笔 behavior-preserving convergence commit；parity、lock 或 error-contract 失败时整笔回退，
不得临时恢复 runtime dual path。

## Slice C — Restore Provider-Neutral Invariant Locality

### Target Architecture

保持 `video_requirement.py` 为 stable public model/hash/serialization interface；本 Slice 不搬迁 public model
classes，以避免改变 class `__module__`、repr/pickle identity或扩大 historical-hash-sensitive edit surface。
只将 neutral rules聚合到一个 private deep implementation：

```text
video_requirement.py                    stable public models/interface
  -> _video_requirement_invariants.py   intrinsic intent/requirement rules,
                                        version compatibility diagnostics
  -> sealed + strictly reopened requirement
       ├─ Shot Router
       └─ _h3_prompt.py                 H3-only expressibility + grammar
```

`video_requirement.py` 的 stable interface 独占 concrete `ProviderNeutralVideoRequirement` strict model reopen与hash
验证，再把 non-persisted facts交给 `_video_requirement_invariants.py`。private implementation不 runtime-import
concrete requirement models；type-only imports或structural facts可用，但不得接收 model class/callback、复制 serialized
schema或建立第二 hash owner。这样可删除 validator local imports并保持单向 dependency。

`validate_causal_transition_readiness()` 同时依赖 previous Shot state 与 transition policy，因此迁移到现有
`video_transition.py` owner，由 `ShotReadinessGate` 消费。`_h3_prompt.py` 不再组合多个 granular neutral validators，
但必须在 expression 前调用 stable neutral strict-reopen/validation interface；它不能信任 nominal Pydantic type，
因为 `model_construct()` / `model_copy(update=...)` 可绕过 validators。historical requirement仍只由 neutral owner
解释 compatibility，H3只检查 native grammar的 expressibility，并保持 exact typed diagnostics。

### Single Owner And Old Path

- Stable public model/interface与concrete strict reopen/hash owner：`video_requirement.py`。
- Intrinsic intent/requirement/version diagnostic rules owner：`_video_requirement_invariants.py`。
- Causal transition readiness owner：`video_transition.py`。
- Provider adapter owner：`_h3_prompt.py` 只保留 H3 expressibility/grammar。
- Retire：`_video_intent_validation.py`、model validators 中的 local-import cycle、H3 对 neutral validators 的
  横向调用、H3 内的 neutral compatibility diagnostic filtering。
- `_video_intent_validation.py` 是 private module；repository callers迁移并证明 zero imports 后删除，不保留
  pass-through壳。若 implementation前发现真实 external consumer，必须停下做 compatibility decision。

### Owned Files

Create：

- `src/ai_video/production/_video_requirement_invariants.py`

Modify/retire：

- `src/ai_video/production/video_requirement.py`
- `src/ai_video/production/_video_intent_validation.py`（delete after migration）
- `src/ai_video/production/_h3_prompt.py`
- `src/ai_video/production/video_transition.py`
- `src/ai_video/planning/video_planner.py`
- `src/ai_video/quality_gates/shot_readiness_gate.py`
- `tests/test_production_video_requirement.py`
- `tests/test_production_video_intent_validation.py`（repurpose to stable public invariant interface）
- `tests/test_production_h3_prompt.py`
- `tests/test_production_video_transition.py`
- `tests/test_planning_video_planner.py`
- `tests/test_shot_readiness_gate.py`

Conditional only if contract text changes：

- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `.agent/harness/policy.yaml` and `tests/test_agent_harness.py` only if the new private path is not already mapped。

Explicitly unchanged：

- `shot_router.py` Provider/profile selection semantics。
- `video_compiler.py` sole `VideoGenerationRequest` construction ownership。
- Provider capability matrices、Manifest/state、Provider lifecycle。

### Milestones

1. **Freeze hash and compatibility behavior**
   - 先记录 requirements `/1`–`/4`、intent projections `/1`–`/3` 的 exact serialized bytes与hash。
   - RED coverage 必须从 public model creation/reopen、planner projection、H3 compile seam 证明 invalid neutral
     state fail closed；不得只断言 helper return。
   - 覆盖 `model_construct()`/tamper bypass、legacy-absent fields、audio forbidden、conditioning lane、camera/subject
     relation 与 geometry/duration mismatch。
   - 锁定 H3 prompt text/hash、unsupported diagnostics order、Router bound request hash与compiler lineage identities。

2. **Introduce one deep invariant implementation**
   - 聚合 intent completeness、camera/subject relation、conditioning与requirement version compatibility。
   - `video_requirement.py` 提供 aggregate strict reopen/validation interface，不让 callers组合 granular helpers。
   - private implementation只计算 diagnostics，不 runtime-import façade、不持久化 fact view、不接收 model class/callback，
     不复制 hash/serialization owner。
   - public model classes留在 `video_requirement.py`，schema-version/historical absence interpretation由 neutral owner完成。

3. **Retire the mixed validator owner**
   - `video_planner.py` 通过 stable neutral interface判断 intent completeness。
   - `validate_causal_transition_readiness()` 移入 `video_transition.py`；`ShotReadinessGate` 改用该 owner。
   - 删除 `_video_intent_validation.py`；`rg` 必须证明 repository 内无旧 import/symbol。

4. **Make H3 fail-closed but expression-only**
   - `compile_h3_prompt()` 先通过 stable neutral interface strict-reopen/validate exact requirement，捕获
     `model_construct()` / `model_copy(update=...)` bypass；不得自行复制 neutral rules。
   - validated current requirement再进入 H3-native expressibility/grammar；historical inputs由 neutral owner解释
     compatibility，H3只检查生成 exact grammar所需 facts并保持 unsupported paths/order。
   - direct helper tests迁移到 public model/planner/transition/H3 interfaces。
   - structural test禁止 `_h3_prompt.py` import neutral private implementation或重引入 diagnostic filters。

5. **Update canonical contracts only after proof**
   - contract matrix 继续声明 neutral requirement owner、Router owner、compiler owner与H3 mechanical adapter。
   - runtime baseline 只记录已通过 compatibility/focused/Harness proof 的 current behavior。

### Acceptance Criteria

- public model classes与imports留在 `video_requirement.py`，class identity与serialization surface不因本 Slice迁移。
- `video_requirement.py` 与 invariant implementation只有单向 runtime dependency，neutral rules只有一个 owner。
- `_video_intent_validation.py` 已删除，repository内无旧 import。
- model/planner通过 stable neutral interface消费 rules；causal Gate从 `video_transition.py` 消费 readiness。
- H3 通过 stable neutral strict-reopen/validation fail closed，不复制 rules或过滤 neutral compatibility diagnostics。
- `/1`–`/4` serialized bytes、hashes、reopen 与 tamper failure behavior bit-for-bit不变。
- Router selection、provider-bound prompt-free request、compiler ownership与H3 three-field grammar不变。
- 没有新增 Provider-specific field、fallback、schema version 或 persisted diagnostic state。

### Focused Verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_production_video_intent_validation.py \
  tests/test_production_h3_prompt.py \
  tests/test_production_video_transition.py \
  tests/test_shot_readiness_gate.py \
  tests/test_planning_video_planner.py \
  tests/test_production_shot_router.py \
  tests/test_video_compiler_c4_qualification.py -q
python -m scripts.architecture_gate check
git diff --check
python -m scripts.agent_harness inspect --staged
python -m scripts.agent_harness verify --staged
python -m scripts.agent_harness verify-receipt <receipt-path>
```

### Rollback

以 invariant extraction、mixed-validator retirement、H3 migration作为可单独验证但连续的 commits。若 historical
hash、class identity、diagnostic order、bypass、planner、transition Gate 或 H3 parity任一失败，回退当前 milestone；不得同时
保留 new private rules与 old `_video_intent_validation.py` 两个 active owners。新 private source path 若未被
Harness policy映射，不得形成 completion receipt。

## Slice B — Deepen VideoGenerationService Lifecycle Choreography

### Target Architecture

`VideoGenerationService` 继续是唯一 generated-video lifecycle orchestration interface。submit 使用互斥 typed
`LocalSubmitContext` / `PaidSubmitContext`；poll/fetch 根据 reopened durable attempt evidence选择 lane，caller
不再在 submit/poll/fetch 三个 phase重复 dispatch。

由于 local 与 paid 已有两个真实 Provider interfaces，允许新增一个 private lane adapter module。该 adapter
只规范 Provider-facing preview/submit/status/fetch 与 typed submit prerequisites；它不得写 Manifest、mint permit、
决定 phase、retry/recover 或 activate。所有 durable choreography 仍由 `VideoGenerationService` 调用
`ProductionStateCommitter` 完成。

```text
caller
  -> service construction binds one Provider lane
  -> submit typed context / poll-once / fetch-once / validate-once / activate-once
       (one requested lifecycle action; at most one Provider effect plus required writes)
  -> VideoGenerationService reads exact state and dispatches private lane
  -> ProductionStateCommitter remains sole state writer
```

canonical target surface 为：

```text
start(...)
submit_attempt_once(..., submission_context=LocalSubmitContext | PaidSubmitContext)
poll_once(attempt_id=...)
fetch_once(attempt_id=...)
validate_once(...)
activate_once(...)
resume_next_action(...)
```

local guard 与 paid preview/reservation使用互斥 typed context，禁止把它们压成一组 nullable parameters。
`submit_attempt_once()` 必须用 reopened exact request/execution identity验证 context；mixed/mismatched context在 preview、intent、
permit和Provider effect前fail closed。`poll_once()` / `fetch_once()` 不接受 caller lane hint。
`resume_next_action()` 继续是 read-only projection，不得维护第二 phase table或自行执行 action。

### Compatibility Strategy

这是分阶段 migration，不直接删除 public methods：

1. 新增 private lane seam 与 canonical typed-context operations。
2. 迁移 `EcommerceShotFacade`、M0/source operators 到 canonical operations。
3. 现有 remote `submit_once(paid_preview, reservation_id)`、`submit_local_once()`、`refresh_once()`、
   `refresh_local_once()` 与 `fetch_local_once()` 暂时作为 thin compatibility adapters，必须委托
   `submit_attempt_once()` / `poll_once()` / common `fetch_once()`；不使用同名 overload或optional-parameter dispatch。
4. `fetch_and_activate()` 保留 current exact-active replay与combined legacy behavior，但 new staged control
   不得调用它；`validate_once()` / `activate_once()` 继续 canonical。
5. 只有 separate public-contract approval、external consumer inventory、release/migration guidance完成后，
   才能删除 compatibility methods。不得以 repository 内 caller 已迁移作为充分证据。

### Single Owner And Old Path

- Single lifecycle interface owner：`VideoGenerationService`。
- Single durable owner：`ProductionStateCommitter`。
- Real adapters：local `LocalVideoProvider` lane 与 paid/remote `VideoProvider` lane。
- Retire in-repo duplicate：`EcommerceShotFacade` 的三处 lane branch；M0/source operators与qualification callers
  的 local method选择。
- Compatibility-only：lane-specific public wrappers 与 `fetch_and_activate()` compound path。current
  `ContinuityReviewCoordinator` 是后者的真实 production consumer，未迁移前不得宣称 full retirement。
- Forbidden alternate path：caller/direct Provider invocation、adapter-side state write、automatic chain、fallback、retry、
  activation或recovery。

### Owned Files

Expected create：

- `src/ai_video/production/_video_generation_lane.py`：private lane interface与两个 real implementations；
  no committer/state ownership。

Expected modify：

- `src/ai_video/production/video_generation.py`
- `src/ai_video/production/ecommerce_ad_coordinator.py`
- `src/ai_video/production/shot_continuity_m0_operator.py`
- `src/ai_video/production/shot_continuity_source_operator.py`
- `src/ai_video/production/shot_continuity_m0_caller.py`
- `src/ai_video/production/shot_continuity_source_qualification.py`
- `src/ai_video/production/continuity_review_coordinator.py` only in separately approved full
  `fetch_and_activate()` retirement。
- `tests/test_video_generation.py`
- `tests/test_production_local_video_state.py`
- `tests/test_production_generated_video_e2e.py`
- `tests/test_production_continuity_review_coordinator.py`
- `tests/test_production_ecommerce_ad_coordinator.py`
- `tests/test_shot_continuity_m0_caller.py`
- `tests/test_shot_continuity_m0_validation.py`
- `tests/test_shot_continuity_m0_operator.py`
- `tests/test_shot_continuity_source_qualification.py`
- `tests/test_shot_continuity_source_runtime.py`
- `tests/test_shot_continuity_source_operator.py`
- `tests/test_production_video_state_recovery.py`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`

Expected unchanged unless a minimal typing import is proven necessary：

- `video.py` / `local_video.py` Provider effect contracts。
- `state_commit.py` and private committer implementations。
- Provider adapters、Manifest schema、recovery entrypoints。

`LocalSubmitContext` / `PaidSubmitContext` 属于 caller-visible canonical signature，必须定义并从 stable
`video_generation.py` interface导出；不得只藏在 private lane module。

### Milestones

1. **Freeze the lifecycle matrix with RED characterization tests**
   - 建立 local/paid × REQUEST/SUBMIT/POLL/FETCH/VALIDATE/CANDIDATE/ACTIVATE matrix。
   - 每个 case 记录 allowed method、return type、exact committer writes、Provider call count与zero-effect failures。
   - 明确 current `fetch_and_activate()` combined compatibility与exact-active read-only replay。

2. **Introduce typed private lane adapters**
   - `LocalSubmitContext` 包含 approved `pre_submit_guard`；`PaidSubmitContext` 包含 exact
     `PaidProviderCallPreview` 与 `reservation_id`。
   - adapter只翻译 Provider operations/results，不读取或写入 Manifest，不持有 recovery/activation logic。
   - submit前拒绝 mixed local+paid prerequisites；poll/fetch从 durable evidence判定 lane。

3. **Centralize lane dispatch inside the service**
   - canonical operations先从 committer重开 exact attempt/request与phase，再选择匹配的 lane。
   - submit 保持 durable intent/one-use permit紧邻 effect；poll/fetch 保持 exact receipt与held-FD sink semantics。
   - 一次调用只执行一个 requested lifecycle action；submit可紧邻完成 intent/effect/outcome writes，
     但不得继续poll/fetch。phase mismatch返回既有 typed `AiVideoError`，不自动执行 next action。

4. **Migrate in-repo callers**
   - `EcommerceShotFacade` 的 service instance绑定一次 Provider lane；submit提供 typed context，poll/fetch删除分支。
   - M0/source operators与qualification callers复用 canonical service；仍由 operator显式检查 requested action，
     不自动循环。
   - caller tests只断言 public observable lifecycle，不 mock private lane implementation details。

5. **Reduce old surface to compatibility adapters**
   - lane-specific wrappers全部委托 canonical implementation，structural test禁止第二套 state/effect choreography。
   - `validate_once()` 必须继续不调用 `fetch_and_activate()`。
   - 若获得 separate public-contract approval，先迁移 `ContinuityReviewCoordinator` 为 explicit
     fetch → validate → activate，证明 validation failure不能activate，再删除 `fetch_and_activate()`。
   - 未获该 approval时，本 Slice在 compatibility阶段结束并明确报告 full retirement未执行。

6. **Prove safety and recovery semantics**
   - local：guard before preview + same guard inside intent lock、stack drift、known-no-effect、unknown outcome、zero resubmit。
   - paid：preview/budget/egress/auth/permit binding、known-no-effect vs unknown outcome、no permit remint。
   - both：reopen phase legality、poll/fetch exact identity、candidate not activation、explicit activation、exact replay zero writes。
   - only after focused/full required tests pass, update canonical docs and baseline。

### Acceptance Criteria

- migrated in-repo callers不再自行选择 local/remote poll/fetch methods；submit调用
  `submit_attempt_once()` 并使用exact typed context。
- service interface继续 phase-explicit；没有 `run_until_complete()`、background loop或automatic next action。
- local/paid submit prerequisites用互斥 typed contexts表达，没有 nullable-parameter soup。
- adapters没有 `ProductionStateCommitter` write/recovery/activation authority。
- provider call count、Manifest revisions、typed errors、receipt/hash identity与return types保持 current contract。
- `validate_once()`只 prepare candidate；`activate_once()` only explicit activation。
- `fetch_and_activate()` compatibility behavior与exact-active replay保持，且没有 new staged caller。
- unknown outcome、reopen/recovery与exact replay regressions全部有 executable proof。

### Focused Verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_video_generation.py \
  tests/test_production_local_video_state.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_continuity_review_coordinator.py \
  tests/test_production_ecommerce_ad_coordinator.py \
  tests/test_shot_continuity_m0_caller.py \
  tests/test_shot_continuity_m0_validation.py \
  tests/test_shot_continuity_m0_operator.py \
  tests/test_shot_continuity_source_qualification.py \
  tests/test_shot_continuity_source_runtime.py \
  tests/test_shot_continuity_source_operator.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_recovery.py -q
python -m scripts.architecture_gate check
git diff --check
python -m scripts.agent_harness inspect --staged
python -m scripts.agent_harness verify --staged
python -m scripts.agent_harness verify-receipt <receipt-path>
```

### Stop Conditions And Rollback

立即停止该 Slice，若 implementation 需要：

- 改变 public CLI、Manifest/schema/layout；
- 新增 lifecycle writer、automatic retry/recovery/activation；
- 放宽 local guard、Paid Provider Gate、unknown-outcome 或 exact replay semantics；
- 让 adapter读取/写入 canonical state；
- 通过 fallback同时保留两套 active choreography。

rollback unit 至少分为 lane seam、caller migration、compatibility adapters 三个可验证 commits；每个 commit
都必须保持 runtime可用。若 caller migration失败，回退 caller commit，不恢复第二套 service implementation。

## Execution Order And Checkpoints

### Checkpoint 0 — Shared Preflight

- 检查 current `git status`、live agent target files与exact overlap。
- 对每个 Slice 运行 Harness `inspect`，确认真实 changed-path checks。
- 记录 exact base commit；不得把 concurrent moving `HEAD` 或 unrelated dirty files带入 receipt。
- 每个 Slice开始前重新运行 relevant Agent Memory RAG；retrieval只是 advisory，current code/tests优先。

### Checkpoint 1 — Slice A

- RED characterization → one deep implementation → old path deletion → focused tests。
- 使用 `reviewer_xhigh`，因为 retrieval/authority/fallback semantics 容易通过普通 tests但产生 semantic drift。
- exact staged Harness PASS 后独立 commit。

### Checkpoint 2 — Slice C

- Freeze historical hashes → neutral interface → consumer migration → old helper retirement。
- 使用 `reviewer_xhigh`，因为 change影响 cross-module requirement/compiler/adapter contract与historical compatibility。
- exact staged Harness PASS 后独立 commit。

### Checkpoint 3 — Slice B

- Freeze lifecycle matrix → private lane seam → service dispatch → caller migration → recovery proof。
- 使用 `reviewer_xhigh`；只有该 tier后仍存在有证据的 critical contradiction，才升级 `reviewer_max`。
- 对 paid/remote lane只运行 fake/offline tests；本 Plan不授权 live Provider或paid call。
- exact staged Harness PASS 后独立 commit。

### Checkpoint 4 — Cross-Slice Closure

- 在每个 Slice都已单独 passing 后，运行 policy要求的 combined exact-range Harness。
- 复核 diff 中不存在 dual owners、stale compatibility fallback、unrelated cleanup或orphan files。
- 更新 roadmap/baseline只描述实际完成并验证的 Slice；未执行 Slice保留 `Proposed`。
- 评估并执行 `record-ai-video-session`；record必须准确区分 architecture evidence、runtime evidence与未验证区域。

## Review Contract

每个 independent reviewer 必须返回：

- `Verdict`: `accept` / `accept with concerns` / `reject`。
- `Blocking issues`。
- `Non-blocking concerns`。
- files/tests evidence。
- minimal follow-up。

parent 必须复核重要 claims，尤其是：

- Slice A lock/client-release 与 stale/corruption distinction；
- Slice C historical bytes/hash与 H3/Router/compiler ownership；
- Slice B one-use permit、unknown outcome、exact replay与 activation separation。

review verdict、Harness receipt、technical metric、P6、Final Acceptance 与 human visual verdict互不替代。

## Definition Of Done

单个 Slice 只有同时满足以下条件才可标记 complete：

- single owner与canonical interface在 code/tests 中可验证；
- old active path已删除，或被明确限制为无业务逻辑的 compatibility adapter；
- unchanged contracts有 positive、negative、replay/tamper或failure-path evidence；
- focused tests、Architecture Gate与exact staged Harness receipt fresh PASS；
- `reviewer_xhigh` 无 blocking issue，parent复核完成；
- exact task-owned files已独立 commit，unrelated dirty/staged work未被覆盖或纳入；
- canonical docs只陈述实际验证后的 current behavior；
- no Provider/media/paid/Production acceptance claim被虚构。

整个 Plan 只有三个 Slice均分别达到上述标准并通过 combined exact-range verification 后才 complete；
部分完成必须逐 Slice报告，不能用总分掩盖未执行或 `NOT_EVALUATED` 的 contract。
