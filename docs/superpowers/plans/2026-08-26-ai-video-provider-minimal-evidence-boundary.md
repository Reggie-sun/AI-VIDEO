# AI-VIDEO Provider-Minimal Evidence Boundary Implementation Plan

## Status

Complete。Milestones 1-5的offline implementation、executable closure与canonical truth同步均已完成。
Exact implementation range `0f73c53..9e999d1` 已通过focused tests、
native `reviewer_xhigh`与fresh exact-range Harness。Offline minimal Provider到达canonical
`CANDIDATE`，没有自动activation。

本completion不授权或证明credential lookup、Paid Provider submit、ComfyUI execution、媒体生成、
Gate 2、P6、Final Acceptance、push或release。Canonical contract matrix、runtime baseline与roadmap只
记录offline executable evidence；现有Harness policy已完整映射implementation paths，因此没有为本slice
新增或复制routing owner。

## Goal

让一个 cloud Provider 只凭：

```text
job_id + status + re-queryable output_url
```

即可沿 AI-VIDEO canonical lifecycle 到达：

```text
sealed neutral requirement
  -> exact Provider/profile/capability selection
  -> compiled + resolved AI-VIDEO request
  -> durable submit/status lineage
  -> committer-owned fetch sink
  -> exact local SHA/probe/decode/measurement
  -> prepared CANDIDATE
```

Provider 只负责生成、状态与输出定位；AI-VIDEO 继续独占 request/Shot/plan/policy/attempt identity、
input hashes、artifact proof 与 downstream acceptance evidence。

本 slice 的自然停止点是 `VideoGenerationService.validate_once()` 完成 canonical candidate preparation。
不得自动调用 `activate_once()`，也不得把 candidate、Provider success 或 probe PASS 描述为 Gate 2、P6
或 Final Acceptance。

## Scope

### In Scope

- 在 pure provider compiler 阶段拒绝 remote one-shot/non-requeryable output capability；
- 新增独立、sealed `output_recovery_strategy` capability declaration，避免把job/status lookup与output
  locator recovery混为一谈；
- 把 serialized `provider_file_id` 固定解释为 opaque output-handle identity，不要求 Provider
  存在 durable file object；
- Seedance status/fetch 不再因缺失 optional `model` echo 而失败；
- MiniMax H3 status/fetch 不再把 echoed resolution/duration/ratio 当作 fetch/probe prerequisite；
- 保留 exact task/effect binding、unknown-status fail-closed、URL origin/size/content-type safety；
- 由 AI-VIDEO 对 fetched exact bytes 计算 SHA、probe 并验证 resolved output contract；
- 证明 `VideoProvenanceReceipt.model_id` / `profile_sha256` 是 requested/selected lineage，不是
  Provider-observed actual execution；
- 证明 local T8/ComfyUI workflow/model/sampler/scheduler seals 没有进入 neutral requirement、Gate 或
  Final Acceptance contract；
- 保持所有 historical request/observation/fetch/provenance bytes、schema 与 fingerprints 可严格 reopen；
- 以additive capability compatibility branch让historical profiles在缺少新字段时保持原bytes/hash，
  但禁止它们用于新的remote attempt。

### Out Of Scope

- 不新增 `ProviderOutputHandle` wrapper、Manifest field、receipt schema/version 或 raw URL persistence；
- 不新增 generic Provider-native claim subsystem；
- 不实现 Gate 2、two-stage quality coordinator、P6 closure 或 Final Acceptance E2E；
- 不改变 candidate activation、repair、review、Final Acceptance 或 lifecycle writer ownership；
- 不修改 Provider ranking、fallback、retry、automatic selection 或 unknown-outcome semantics；
- 不改变 Paid Provider budget、egress、secret、durable intent、one-use permit 或 reservation contract；
- 不改变 Local T8/ComfyUI execution profile、workflow graph、model/component hash 或 runtime behavior；
- 不调用任何 Provider、network、credential、ComfyUI 或 media-generation surface；
- 不声称 MiniMax、Seedance、Hailuo、Veo 或其他 Provider 已获得 live/media/quality acceptance。

## Contract Surfaces

| Surface | Single owner | Target contract |
| --- | --- | --- |
| provider-neutral intent | `ProviderNeutralVideoRequirement` | 保持无 Provider/model/workflow/runtime internals |
| exact selection | Shot Router + `VideoCapabilityVariant` | selected `output_recovery_strategy`进入capability/profile fingerprint与provider-bound identity |
| pre-start recovery eligibility | `compile_provider_video_request()` | remote capability缺少supported strategy时返回typed unsupported；不创建attempt/intent/permit/effect |
| resolved request lineage | selected adapter `resolve()` + existing request models | requested Provider/model/profile/Shot/assets/compiler identity 不变 |
| status/output handle | selected adapter | same task/effect ID、typed state、successful opaque handle；optional metadata 不能成为 universal prerequisite |
| durable lifecycle | `ProductionStateCommitter` | 继续独占 status/fetch/candidate/activation/recovery writes |
| fetched bytes | selected adapter + committer sink | transport safety、stream size/SHA、no raw URL persistence |
| exact media proof | `video_artifact.py` + probe owner | reopen exact bytes、recompute SHA、decode/probe、compare resolved output |
| quality/acceptance | existing Gate/Review/P6/Final Acceptance owners | 只消费 exact media、AI-VIDEO lineage 与 required evaluator/human evidence |

## Architecture Decision

### Selected MVP: Additive Recovery Strategy, Preserve Receipt Schemas

现有`VideoCapabilityVariant.lookup_supported`只说明Provider可按effect/job identity执行lookup。它不能
区分：

- lookup返回stable file ID；
- lookup每次返回可轮换signed URL；
- status可lookup，但output URL只在一次response中出现且无法恢复。

因此不能把`lookup_supported=True`重新解释为output recovery guarantee。MVP在
`VideoCapabilityVariant`新增optional、backward-compatible `output_recovery_strategy`：

```text
DURABLE_FILE_ID
REQUERY_BY_EFFECT_ID
NON_RECOVERABLE_EPHEMERAL_URL
```

Historical payload缺少该字段时解析为`None`，serializer与canonical capability projection必须在值为
`None`时省略字段，从而保持historical capability/profile JSON与hash不变。新的remote selected
capability必须显式选择一个strategy；只有前两项可compile。`None`与
`NON_RECOVERABLE_EPHEMERAL_URL`都不得用于新的remote attempt。Local capability保持`None`，其现有
local lifecycle不在此cloud contract内。

Current adapter mapping：

- Seedance：`REQUERY_BY_EFFECT_ID`；
- MiniMax H3：`REQUERY_BY_EFFECT_ID`；
- MiniMax Hailuo：`DURABLE_FILE_ID`；
- Local T8/ComfyUI：`None`，保持local-specific lifecycle。

新字段自然进入current capability fingerprint；Seedance selected profile hash也必须随new capability
bytes变化。Historical profile缺字段时仍严格reopen且hash不变。Implementation不得覆盖historical
profile artifact，也不得用old profile pointer创建new remote attempt。

实现新增 `ProviderRequirementUnsupportedReason.OUTPUT_LOCATOR_NOT_RECOVERABLE`。在
`compile_provider_video_request()` 完成 exact selected-capability identity validation后、创建
`VideoGenerationRequestCompilation` 前执行：

```text
if capability.execution_kind is REMOTE and capability.output_recovery_strategy not in {
    DURABLE_FILE_ID,
    REQUERY_BY_EFFECT_ID,
}:
    unsupported(
        reason=OUTPUT_LOCATOR_NOT_RECOVERABLE,
        unsupported_field_paths=("selection.output_recovery_strategy",),
    )
```

`require_compiled_provider_request()` 继续把 typed reason 映射为现有
`ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED`；不新增 ErrorCode、schema 或 lifecycle state。

### Adapter-Owned Opaque Handle Strategies

Generic serialized field继续名为`provider_file_id`，但 source docstring、tests 与 canonical docs必须明确：
它表示 opaque output-handle identity。

| Adapter | Opaque handle semantics | Fetch recovery |
| --- | --- | --- |
| MiniMax Hailuo | Provider返回stable file ID | 用same file ID做file retrieve；status/fetch间变更必须fail closed |
| Seedance | exact task/effect ID的deterministic derived handle | 用same task ID重新query current signed URL；URL可轮换 |
| MiniMax H3 | exact task/effect ID的deterministic derived handle | 用same task ID重新query current signed URL；URL可轮换 |

Raw signed URL不进入Manifest、observation/fetch/provenance receipt、normal logs或errors。URL本身不参与
result identity；identity来自exact submit effect、opaque handle与最终artifact SHA。

若future Provider可查询status但只能返回一次性不可重取URL，它必须声明
`NON_RECOVERABLE_EPHEMERAL_URL`并在compiler阶段被拒绝；不得谎报`REQUERY_BY_EFFECT_ID`。
Secret-safe durable locator或observe-and-fetch atomic transaction需要独立spec，不得用process-local
cache绕过。

### Optional Native Metadata Semantics

Status parsing按以下规则实现：

| Field | Absent | Present and matching | Present and conflicting |
| --- | --- | --- | --- |
| exact task/effect ID | fail closed | continue | fail closed |
| typed status | fail closed | continue | unknown status fail closed |
| successful output URL/handle | success state时fail closed | continue | invalid locator fail closed |
| echoed model | `UNAVAILABLE`，不阻塞 | adapter-specific observation only | 与sealed `provider_task_binding.response_model_id`冲突，按`UNKNOWN` fail closed |
| echoed resolution/duration/ratio | `UNAVAILABLE`，不阻塞 | advisory only | 不决定media acceptance；由local probe裁决actual output |
| seed/scheduler/revision/workflow | `UNAVAILABLE`或`NOT_APPLICABLE` | 无accepted consumer时不持久化 | 不伪造、不转换为Gate truth |

`provider_task_binding.response_model_id`继续表示selected adapter对可用model echo的exact conflict
binding；它不把model echo变成status成功的必填字段，也不把Provider claim升级成Final Acceptance truth。

## Invariants

- `ProviderNeutralVideoRequirement` 不新增 Provider/model/seed/scheduler/workflow/payload字段；
- Router 仍是唯一 Provider/profile/capability selector，不ranking、不fallback；
- compiler只做pure mechanical compilation和typed unsupported，不执行IO或lifecycle mutation；
- `ProductionStateCommitter`仍是唯一v2 write/activation/recovery owner；
- `VideoGenerationService.start()`不承担output-recovery discovery；unsupported必须更早在compiler阻断；
- exact replay不重复Provider、fetch、probe、committer或activation side effect；
- success observation必须绑定same submission/effect与opaque handle；
- fetch receipt SHA/size与held artifact/probe必须一致；Provider声明不能覆盖local measurement；
- missing semantic/domain/human evidence继续产生`NOT_EVALUATED`；Provider success不能抵消；
- `output_recovery_strategy`变化必须改变current capability/profile/provider-bound identity；historical
  payload缺字段时仍按原bytes/hash reopen，且不得用于new remote attempt；
- local T8-specific workflow/component/scheduler/sampler/node facts保留在local profile/adapter，不进入
  cloud-neutral contract；
- 本 slice不新增writer、fallback、retry、automatic activation或automatic Final Acceptance。

## Current And Target Behavior

| Surface | Current behavior | Target behavior |
| --- | --- | --- |
| capability | 只有generic `lookup_supported`，无法区分status lookup与output recovery | additive explicit recovery strategy；legacy absence保持hash但不能创建new remote attempt |
| compiler | selected capability identity已校验，但remote output recovery未作为typed pre-start denial | unsupported/absent strategy返回`OUTPUT_LOCATOR_NOT_RECOVERABLE` |
| Seedance query | `model`缺失或不等于expected即失败 | 缺失允许；present conflict仍按exact binding fail closed |
| MiniMax H3 query | 强制task model/resolution/duration/ratio全量回显 | task/status/URL required；model conflict fail closed；output-profile echo不再是prerequisite |
| Hailuo query/fetch | task/status/file ID + local download SHA | 保持reference behavior |
| observation/fetch | `provider_file_id`参与existing fingerprints | bytes/hash不变，只明确为opaque handle |
| provenance | `model_id/profile_sha256`来自resolved request | 明确为requested/selected lineage，不声称actual Provider execution |
| artifact validation | local SHA/probe重新验证bytes | 保持唯一media-proof owner |
| Gate/P6/Final Acceptance | schemas不要求Provider internals | 增加negative boundary tests，不改owner或schema |

## Compatibility

### Serialized Contracts

以下类型不得增加、删除、重命名或改变serialized field：

- `VideoGenerationRequest`；
- `ResolvedVideoGenerationRequest`；
- `VideoSubmission`；
- `VideoTaskObservation`；
- `VideoFetchReceipt`；
- `VideoProbeReceipt`；
- `VideoProvenanceReceipt`；
- Manifest video-generation pointers/state。

`provider_file_id`继续直接参与observation、fetch与provenance fingerprints。实现只改变adapter解析要求和
字段解释，不改变历史JSON bytes/hash。

### Capability Identity

新增optional `output_recovery_strategy` capability field，并使用explicit compatibility projection：

- `None`时serializer与`project_capability_variant()`省略该key，historical variant/profile hash不变；
- current remote variants必须显式设置，strategy进入capability fingerprint；
- Seedance profile hash随current selected capability bytes改变，new profile pointer必须使用new hash；
- Router selected capability fingerprint与provider-bound request hash随strategy改变；
- historical capability/profile/request fixture仍按原bytes与hash reopen；
- historical remote strategy `None`不能compile new attempt；
- local strategy `None`继续可compile；
- strategy变化不能在已有attempt内静默替换resolved request。

### Compiler Identity

本slice不改变`AdapterCompilerContract` schema、hash算法或现有Seedance/H3/Hailuo compiler version `1`。
Output recovery由new capability field绑定；response-parser relaxation属于status adapter bug fix，不改变
neutral-to-native request compilation grammar。若implementation evidence证明现有compiler version contract
确实包含response metadata grammar，则触发stop condition并提出独立version/compatibility decision，
不得在本slice静默重写historical compiled hashes。

## Old-Path Retirement

Implementation必须删除或约束以下behavior：

1. Seedance `_query()` 不得把absent optional `model`当作Provider failure；
2. MiniMax H3 `_query()` 不得要求resolution/duration/ratio echo才能进入fetch；
3. MiniMax H3 output-profile echo不得代替local probe或让invalid bytes通过；
4. absent或non-recoverable remote strategy不得在attempt/intent/permit/submit之后才暴露unsupported；
5. `VideoProvenanceReceipt.model_id`不得被docs/test命名为verified actual model；
6. `provider_file_id`不得被generic contract解释为durable Provider file object；
7. process-local cached URL、raw signed URL persistence、URL hash identity、blind re-query fallback与无exact
   effect lineage的synthetic handle不得出现。

Exact effect ID派生的deterministic handle不是old path，必须保留。

## Unchanged Contracts

- Paid Provider Gate、unknown outcome、reservation settlement、permit one-use与secret rules不变；
- `VideoProvider` protocol的submit/status/fetch method signatures不变；
- `VideoGenerationService` durable phase ordering与explicit `validate_once()`/`activate_once()`分离不变；
- Asset Registry、Dependency Graph、`ResolvedTimeline`、HyperFrames与P4 audio/caption owner不变；
- Gate 1 / Gate 2 taxonomy、P6 adjudication与Final Acceptance rollup owner不变；
- Local T8/ComfyUI profile seals、workflow topology、model bytes与runtime preflight不变；
- Legacy `0.1.x` CLI、Manifest、artifact layout与local-first default不变。

## Implementation File Map

### Runtime Owners

| File | Planned change | Must not change |
| --- | --- | --- |
| `src/ai_video/production/video_compiler.py` | 新增typed unsupported reason；remote output-strategy preflight | selection、fallback、request schema、compiler hash algorithm |
| `src/ai_video/production/video.py` | additive recovery enum/field/legacy serializer；docstring明确opaque handle | request/observation/fetch fields、historical hashes、protocol signatures |
| `src/ai_video/production/_video_capability_fingerprint.py` | `None`时省略新field，set时纳入canonical projection | existing cardinality compatibility、hash owner duplication |
| `src/ai_video/production/video_artifact.py` | docstring明确provenance model/profile是requested/selected identity | provenance fields/hash、probe behavior |
| `src/ai_video/production/seedance_capabilities.py` | current remote variants声明`REQUERY_BY_EFFECT_ID`并校验exact official matrix | model/mode/output matrix、pricing或Provider selection |
| `src/ai_video/production/seedance.py` | optional model echo + exact conflict semantics | submit/Paid Gate、task ID、origin/size safety、request payload |
| `src/ai_video/production/minimax_h3.py` | minimal status parsing；output echo不再阻塞 | submit/Paid Gate、task ID/model conflict、origin/size safety |
| `src/ai_video/production/minimax_hailuo.py` | current remote variants只新增`DURABLE_FILE_ID`declaration | query/fetch/status/payload behavior |

`comfy_t8_video.py`与`comfy_t8_turbo_video.py`原则上只运行regression，不修改。若test证明它们必须
改变，先停止并确认scope；不得以“统一adapter”为理由扩张。

### Focused Tests

| File | Planned coverage |
| --- | --- |
| `tests/test_production_provider_neutral_adapters.py` | remote strategy preflight、fingerprint/profile propagation、no-fallback/local exception |
| `tests/test_production_video.py` | opaque-handle/provenance semantics与historical hash/reopen |
| `tests/test_production_seedance.py` | minimal response、absent model、model/task conflict、unknown status、URL rotation |
| `tests/test_production_minimax_h3.py` | minimal response、optional output echo、model/task conflict、URL rotation、invalid bytes |
| `tests/test_production_minimax_hailuo.py` | stable file-ID regression，无source change |
| `tests/test_production_generated_video_e2e.py` | offline minimal cloud path到CANDIDATE、restart/replay/tamper、zero activation |
| `tests/test_production_quality_gate_coordinator.py` | Provider-native fields不能成为Gate 1 prerequisite |
| `tests/test_production_review.py` | missing required evaluator/human evidence仍为`NOT_EVALUATED`；只运行或在ownership清晰后最小修改 |
| `tests/test_production_comfy_t8_video.py` / `test_production_comfy_t8_turbo_video.py` | local-only seal不泄漏到neutral/Gate contract |

优先复用existing mapped test files，不创建未映射的broad integration test module。若确需新test path，必须
先同步`.agent/harness/policy.yaml`的single routing owner及Harness tests，不能依赖fallback full-tests
掩盖mapping gap。

### Canonical Documentation After Executable Proof

只有上述executable evidence通过后，才更新：

- `docs/agent-primary-contract-matrix.md`：owner、forbidden bypass与focused verification；
- `docs/v0.2-runtime-baseline.md`：已实现offline boundary与明确未验证live/quality边界；
- `docs/v0.2-agentic-production-roadmap.md`：slice status与remaining Gate 2/P6 follow-up；
- 本spec与plan的Status：从`Proposed`更新到exact verified状态。

`.agent/harness/policy.yaml`只在inspection证明changed path没有正确routing时修改；不得为了让receipt通过而
放宽checks或刷新baseline隐藏regression。

## Milestone 1 — Pure Recovery Preflight

### Goal

建立独立于status lookup的sealed output-recovery contract，并在任何attempt、Manifest、Paid intent、
permit、network或Provider effect之前拒绝remote non-recoverable output capability。

### Files

- `src/ai_video/production/video_compiler.py`
- `src/ai_video/production/video.py`
- `src/ai_video/production/_video_capability_fingerprint.py`
- `src/ai_video/production/seedance_capabilities.py`
- `src/ai_video/production/minimax_h3.py`
- `src/ai_video/production/minimax_hailuo.py`
- `tests/test_production_provider_neutral_adapters.py`
- `tests/test_production_video.py`

### RED

先新增tests证明：

1. remote selected capability的strategy为`None`或`NON_RECOVERABLE_EPHEMERAL_URL`时得到
   `ProviderRequirementUnsupported(reason=OUTPUT_LOCATOR_NOT_RECOVERABLE)`；
2. `unsupported_field_paths == ("selection.output_recovery_strategy",)`，且result没有prompt/payload；
3. `require_compiled_provider_request()`返回non-retryable
   `ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED`并保留typed reason detail；
4. compiler denial前后Manifest bytes、committer spy、permit spy、transport spy与Provider call count均为零；
5. local strategy `None`仍可compile；
6. `lookup_supported=True + NON_RECOVERABLE_EPHEMERAL_URL`仍被拒绝，证明两个concern没有混淆；
7. current Seedance/H3/Hailuo分别声明exact expected strategy；
8. strategy变化改变capability fingerprint、Seedance new profile hash、Router decision与provider-bound
   request hash；
9. historical capability/profile payload缺field时strict reopen且原hash不变；
10. historical remote profile缺strategy时不能创建new compiled attempt。

### GREEN

- 新增`VideoOutputRecoveryStrategy`与optional `VideoCapabilityVariant.output_recovery_strategy`；
- 增加legacy-compatible serializer/projection：`None`省略、set值纳入hash；
- current Seedance/H3/Hailuo remote variants声明exact strategy，official Seedance matrix validation也比较该
  field；
- 在compiler reason enum新增`OUTPUT_LOCATOR_NOT_RECOVERABLE`；
- 在exact selected capability validation之后、任何request projection construction之前加入cloud-only
  recovery-strategy check；
- 不新增request/receipt/Manifest field、ErrorCode、IO或fallback；
- 不修改`VideoGenerationService.start()`来补救晚期denial。

### Acceptance

- denial是pure、deterministic、typed、non-retryable；
- selected recovery guarantee已由new additive capability/profile fingerprint承载；
- no-side-effect assertion覆盖attempt、Manifest、permit、network与Provider；
- local lanes与historical serialized hashes不变；current remote profile/capability hashes按new bytes更新。

### Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_shot_router.py \
  tests/test_production_video.py \
  -q
```

## Milestone 2 — Minimal Seedance And MiniMax H3 Status Contracts

### Goal

让两类cloud adapter仅依赖effect identity、typed status与output locator进入fetch，同时保留explicit
conflict与transport safety。

### Files

- `src/ai_video/production/seedance.py`
- `src/ai_video/production/minimax_h3.py`
- `tests/test_production_seedance.py`
- `tests/test_production_minimax_h3.py`
- regression only: `tests/test_production_minimax_hailuo.py`

### RED — Seedance

- query response只有`id + status`时，QUEUED/RUNNING可正常产生observation；
- successful response只有`id + status + content.video_url`时可产生SUCCEEDED与task-derived handle；
- missing `model`不阻塞status或fetch；
- present matching `model`保持兼容；
- present conflicting `model`、changed task ID、unknown status、missing success URL均fail closed；
- status/fetch两次query返回不同signed URL时仍用same task-derived handle下载current URL；
- raw URL不出现在receipt JSON、Manifest、normal error text或artifact metadata。

### RED — MiniMax H3

- task response只有`id + status`时，QUEUED/RUNNING正常；
- successful task只有`id + status + content.url`时可fetch；
- missing model/resolution/duration/ratio不阻塞；
- present conflicting model按sealed task binding fail closed；
- present mismatched resolution/duration/ratio不直接阻塞fetch，也不能覆盖local probe；
- changed task ID、unknown status、missing success content/URL、invalid URL origin均fail closed；
- URL轮换不改变task-derived handle、observation/fetch identity；
- final bytes不符合resolved geometry/duration/codec时由probe失败，而不是由Provider echo裁决。

### GREEN

- Seedance `_query()`保留`expected_model_id`用于“present conflict”判断，但不要求field存在；
- MiniMax H3 `_query()`保留exact task ID、status、success URL和optional model conflict validation；
- 删除resolution/duration/ratio的mandatory equality gate；
- 不保存native response object，不新增claim fields；
- 保留URL allowlist、scheme、credentials exclusion、content type、byte ceiling与download SHA；
- MiniMax Hailuo保持stable file-ID reference implementation，无source change。

### Acceptance

- minimal responses进入fetch；
- unavailable optional metadata不会伪造成selected/default值；
- exact identity conflict与unknown state仍fail closed；
- output truth由local bytes/probe决定；
- Paid Gate与submit request payload完全不变。

### Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_seedance.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_minimax_hailuo.py \
  -q
```

## Milestone 3 — Offline Minimal Cloud Lifecycle To Candidate

### Goal

通过standard production loading/committer/service seam，证明minimal Provider response可以到达exact
fetched/probed candidate，并验证restart/replay与tamper failure。

### Files

- `tests/test_production_generated_video_e2e.py`
- `src/ai_video/production/video.py`（docstring only）
- `src/ai_video/production/video_artifact.py`（docstring only）
- `tests/test_production_video.py`

### Test Fixture Contract

使用offline scripted adapter/transport，不访问network。Provider-visible payload只能包含：

```text
submit: job_id
poll:   job_id + status
ready:  job_id + status + output_url
fetch:  exact MP4 bytes
```

fixture不得注入model、seed、scheduler、revision、workflow、resolution、duration、ratio或Provider SHA。
不得通过裸JSON parsing、直接写Manifest、伪造probe receipt或绕过committer来制造PASS。

### RED

1. neutral requirement -> Router -> compiler -> resolve完整binding成立；
2. `start()`、`submit_once()`、`refresh_once()`、`fetch_once()`按durable phases执行；
3. `validate_once()`读取held exact artifact，重新计算SHA并probe，phase到`CANDIDATE`；
4. test结束时未调用`activate_once()`，attempt仍未被错误描述为Final Acceptance；
5. restart后从durable effect/opaque handle重新query/fetch，不依赖process-local URL；
6. exact replay不重复submit/fetch/probe/committer effects；
7. rotated signed URL不改变opaque handle identity；
8. task ID/observation/fetch lineage替换、truncated/substituted bytes、receipt SHA mismatch与invalid probe都在
   candidate前fail closed；
9. Provider-declaredoutput facts即使存在也不能覆盖local measured metadata；
10. generated provenance中的model/profile等于resolved requested/selected identity，且test明确不声称
    Provider-observed actual execution。

### GREEN

原则上不修改`video_generation.py`、committer或artifact validation implementation；使用existing
`fetch_once()`与`validate_once()`完成slice。若现有owner无法承载minimal response，先证明具体gap；
不得直接扩张service、添加second writer或让adapter自行prepare/activate candidate。

### Acceptance

- exact bytes、fetch receipt、probe receipt、provenance与candidate identity一致；
- restart不需要durable raw URL；
- mutation/tamper在activation之前停止；
- Provider success不会自动激活或完成P6/Final Acceptance。

### Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video.py \
  -q
```

## Milestone 4 — Gate Boundary, T8 Isolation, And Compatibility

### Goal

证明Provider-minimal change只解除adapter response coupling，不把Provider internals移动到Gate、Review、
Final Acceptance或neutral contract。

### Files

- tests only unless a real defect is proven:
  - `tests/test_production_video_requirement.py`
  - `tests/test_production_quality_gate_coordinator.py`
  - `tests/test_production_review.py`
  - `tests/test_production_comfy_t8_video.py`
  - `tests/test_production_comfy_t8_turbo_video.py`
  - `tests/test_production_video.py`

### Required Coverage

- neutral requirement strict models拒绝provider/model/seed/scheduler/revision/workflow/payload fields；
- Gate 1 context/profile/result strict models拒绝Provider-native prerequisite fields；
- accepted Gate 2 target/receipt与Final Acceptance receipt没有Provider-native field；对未accepted dirty
  implementation只验证owner boundary，不把它纳入本slicecompletion；
- missing required evaluator/human evidence保持`NOT_EVALUATED`，Provider success不能转成PASS；
- final acceptance rollup不query Provider；
- T8 exact workflow/component/model/sampler/scheduler/node topology tests保持PASS；
- cloud adapters与Gate models不import T8 workflow/profile internals；
- historical observation/fetch/provenance JSON与hash fixture byte-identical；
- no raw URL、native-claim field、new writer、fallback或automatic activation path。

### Acceptance

- Gate与acceptance contract只看到AI-VIDEO lineage、exact media measurements及evaluator/human evidence；
- T8 strictness仍存在，但只在local adapter/profile；
- 只有backward-compatible capability field addition；无request/receipt/Manifest migration、无alternate
  lifecycle owner；
- existing review/final-acceptance regressions通过。

### Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_production_video_requirement.py \
  tests/test_production_quality_gate_coordinator.py \
  tests/test_production_review.py \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_video.py \
  -q
```

## Milestone 5 — Canonical Truth And Exact-Snapshot Closure

### Goal

只把fresh executable proof同步到canonical docs，并对exact implementation snapshot运行policy-required
Harness。

### Preconditions

- Milestones 1-4 focused tests全部通过；
- target-file ownership已重新检查；
- current dirty canonical docs若仍被其他writer拥有，则停止，不覆盖；
- 未执行Provider/network/media/live acceptance；
- spec/plan Status wording不超出offline evidence。

### Documentation Updates

- contract matrix只记录single owner、forbidden bypass与focused verification；
- runtime baseline只声明offline minimal response与local proof已实现；
- roadmap记录remaining live Provider grammar、media quality、Gate 2/P6/Final Acceptance work；
- spec/plan Status引用exact commit/receipt，不把candidate preparation写成activation/acceptance。

### Harness Sequence

先检查真实changed-path routing：

```bash
python scripts/agent_harness.py inspect \
  --path src/ai_video/production/video_compiler.py \
  --path src/ai_video/production/video.py \
  --path src/ai_video/production/_video_capability_fingerprint.py \
  --path src/ai_video/production/video_artifact.py \
  --path src/ai_video/production/seedance_capabilities.py \
  --path src/ai_video/production/seedance.py \
  --path src/ai_video/production/minimax_h3.py \
  --path src/ai_video/production/minimax_hailuo.py \
  --path tests/test_production_provider_neutral_adapters.py \
  --path tests/test_production_seedance.py \
  --path tests/test_production_minimax_h3.py \
  --path tests/test_production_generated_video_e2e.py
```

随后只stage已确认由本task拥有的exact paths；若其中任一文件仍有其他writer的未提交变化，必须先从
本次implementation scope移除并停止对应milestone，不能把它一起stage：

```bash
git add \
  src/ai_video/production/video_compiler.py \
  src/ai_video/production/video.py \
  src/ai_video/production/_video_capability_fingerprint.py \
  src/ai_video/production/video_artifact.py \
  src/ai_video/production/seedance_capabilities.py \
  src/ai_video/production/seedance.py \
  src/ai_video/production/minimax_h3.py \
  src/ai_video/production/minimax_hailuo.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_video.py \
  tests/test_production_seedance.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_requirement.py \
  tests/test_production_quality_gate_coordinator.py \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md \
  docs/superpowers/specs/2026-08-26-ai-video-provider-minimal-evidence-boundary.md \
  docs/superpowers/plans/2026-08-26-ai-video-provider-minimal-evidence-boundary.md
git diff --cached --name-only
python scripts/agent_harness.py inspect --staged
python scripts/agent_harness.py verify --staged \
  --run-id provider-minimal-evidence-boundary-implementation
python scripts/agent_harness.py verify-receipt \
  .agent/harness/runs/provider-minimal-evidence-boundary-implementation/receipt.json
```

若该run ID已存在，停止并在实际执行记录中选定另一个完整、无占位符的唯一ID，再整体替换上述两处；
不得覆盖或复用旧receipt。Receipt必须证明：

- non-empty exact staged snapshot；
- scope/policy与artifact hashes匹配；
- all required checks PASS；
- freshness、snapshot与integrity validation为true；
- unrelated dirty/untracked work未进入detached execution tree。

### Independent Review

由于change影响Provider lifecycle、recovery、paid execution前置边界与Gate evidence semantics，使用一个
native `reviewer_xhigh`进行read-only review。Reviewer scope只覆盖exact task diff与tests，必须输出：

- `Verdict: accept | accept with concerns | reject`；
- blocking issues与non-blocking concerns；
- source/test evidence；
- minimal follow-up。

Parent必须验证重要claim。修复blocking issue后以同一tier做scoped re-review，不并行调用其他tier。

### Implementation Checkpoint

- Implementation commits：`ab58412`、`dc92020`、`5cb65d1`、`9e999d1`；exact range
  `0f73c53..9e999d1`。
- Milestones 1-4的strict RED/GREEN与focused suites通过；最终capability-focused复核为`202 passed`。
- Offline E2E从neutral requirement、Router、compiler、resolve与service进入fetched/probed
  `CANDIDATE`；fresh adapter instance按effect identity重新查询轮换URL，没有process-local URL cache、
  raw signed URL persistence或automatic activation。
- Native `reviewer_xhigh`在修复capability serialization order regression后scoped re-review为
  `Verdict: accept`，无blocking或non-blocking concern。
- Exact-range Harness receipt：
  `.agent/harness/runs/provider-minimal-evidence-boundary-implementation-20260826-v3/receipt.json`；
  `production_review_tests`为`636 passed`，`production_video_provider_tests`为`696 passed`，
  `provider_neutral_video_requirement_tests`为`300 passed`，Architecture Gate PASS。
- Receipt integrity、freshness、snapshot、policy、scope、cleanup、closure与overall passed验证均为`true`。
- Milestone 5已同步canonical contract matrix、runtime baseline与roadmap；existing Harness policy无需
  变化，所有implementation paths均由现有categories覆盖且receipt没有unmapped/fallback path。

## Test Matrix

| Requirement | Test layer | Expected result |
| --- | --- | --- |
| remote strategy absent/one-shot | compiler unit | typed unsupported before side effect |
| status lookup true but output one-shot | compiler unit | still unsupported；concerns remain separate |
| remote requeryable/durable output | compiler/router | compiled and strategy hash-bound |
| local strategy absent | compiler regression | remains allowed |
| minimal queued/running | adapter unit | typed observation without optional metadata |
| minimal success URL | adapter unit | opaque handle + fetch eligible |
| task/effect mismatch | adapter unit | fail closed |
| model absent | adapter unit | allowed |
| model conflict | adapter unit | fail closed as UNKNOWN conflict |
| output echo absent/mismatch | H3 unit + artifact test | fetch allowed; local probe decides actual output |
| URL rotation | adapter/lifecycle | same opaque handle, current URL fetched |
| raw URL persistence | serialization search/test | absent |
| mutated/truncated/substituted bytes | artifact/lifecycle | fail before candidate/activation |
| restart | lifecycle | recover from effect/handle without process cache |
| replay | lifecycle | zero repeated effects |
| requested model/profile provenance | model/lifecycle | exact resolved identity, no actual-execution claim |
| missing semantic/domain evidence | Gate/Review | `NOT_EVALUATED` |
| T8 internals | local regression + architecture | local seal PASS; neutral/Gate schema rejects leakage |
| historical receipts | compatibility | byte-identical reopen/hash |

## Acceptance Criteria

1. remote strategy缺失或为`NON_RECOVERABLE_EPHEMERAL_URL`时pure compiler返回
   `OUTPUT_LOCATOR_NOT_RECOVERABLE`，且attempt、Manifest、permit、network、Provider calls为零；
2. `lookup_supported=True`不能让one-shot output通过；status lookup与output recovery保持独立；
3. recovery guarantee通过additive capability/profile fingerprint与provider-bound identity绑定；historical
   profile缺field仍按原hashreopen，但不能创建new remote attempt；
4. minimal `job_id + status + re-queryable output_url` offline Provider到达canonical `CANDIDATE`；
5. response不含model/seed/scheduler/revision/workflow/resolution/duration/ratio仍可fetch/probe；
6. task/effect mismatch、unknown status、missing success URL、fetch lineage mismatch均fail closed；
7. Seedance/H3 URL rotation不改变effect-derived opaque handle identity；
8. Hailuo stable file ID变化仍fail closed；
9. artifact SHA、size、decode与probe只由AI-VIDEO exact bytes证明；Provider claims不能override；
10. mutated/truncated/substituted bytes不能到达candidate；
11. `VideoProvenanceReceipt.model_id/profile_sha256`明确且可执行地表示requested/selected identity；
12. missing evaluator/human evidence仍为`NOT_EVALUATED`；Provider success不能推进Gate 2/P6/Final Acceptance；
13. T8 workflow/model/sampler/scheduler/node seals不进入neutral requirement或universal Gate schema；
14. observation/fetch/provenance schema、historical JSON与fingerprints不变；
15. 无raw URL persistence、new writer、fallback、blind retry、automatic activation或automatic Final Acceptance；
16. focused suites与exact-snapshot Harness receipt fresh PASS；
17. canonical docs只声明offline verified boundary，并列出live/media/quality未验证范围。

## Stop Conditions

遇到以下任一情况必须停止当前implementation slice并重新做compatibility/architecture decision：

- 需要迁移Manifest、observation、fetch或provenance schema；
- additive capability field无法在`None` omission下保持historical profile/hash reopen；
- output recovery需要保存secret-like durable locator；
- one-shot Provider只能靠process-local URL cache或same-call download才能工作；
- 需要修改`VideoGenerationService.start()`之后才发现output recovery unsupported；
- 需要新增second writer、automatic recovery、fallback、retry、activation或Final Acceptance；
- optional metadata缺失只能通过伪造seed/model/revision/workflow default绕过；
- implementation需要修改current dirty `video_generation.py`、Review/Ecommerce Gate或canonical docs，且
  exact owner尚未释放；
- tests必须调用Provider、credential、network、ComfyUI或生成媒体；
- compiler version/schema必须变化且没有独立migration decision；
- Gate 2/P6/Final Acceptance closure被证明是完成minimal fetch/probe所必需。

## Rollback

- runtime rollback按adapter拆分：先回退Seedance/H3 optional metadata parsing，再回退compiler remote
  lookup denial；
- 删除新增tests/docstrings与canonical doc statements，但不重写historical artifacts；
- 已存在durable attempt时继续走existing explicit recovery，不删除complete orphan evidence、不blind retry；
- rollback不得重新引入raw URL persistence、second writer、fallback或Provider-claimed media measurements；
- 若rollback会让absent/non-recoverable remote strategy在submit后才失败，必须先停止new attempt
  creation，再执行
  explicit recovery。

## Definition Of Done

只有以下条件全部满足，implementation才可宣称完成：

- Milestones 1-4的RED/GREEN与focused verification均通过；
- minimal cloud offline lifecycle到达CANDIDATE但没有自动activation；
- Seedance、MiniMax H3、MiniMax Hailuo与Local T8边界均有executable regression evidence；
- historical schema/hash/reopen与old-path retirement有tests保护；
- exact staged snapshot或exact commit range产生fresh passing Harness receipt并验证；
- `reviewer_xhigh`无blocking issue，parent已验证关键review claims；
- canonical docs与spec/plan Status只记录实际offline proof；
- final delivery明确列出changed files、tests、receipt、commit/publication state与remaining live/media/quality
  uncertainty；
- substantial checkpoint已按`record-ai-video-session`规则评估并记录；
- 没有Provider call、credential lookup、network、ComfyUI或媒体生成。
