# Provider-Minimal Evidence Boundary Specification Record

Date: 2026-08-26

## Purpose

本文记录 `docs/superpowers/specs/2026-08-26-ai-video-provider-minimal-evidence-boundary.md`
达到稳定 documentation checkpoint 时的 verified scope、关键架构决定与证据边界。详细 contract
以该 Spec 为唯一 owner；本记录不复制字段 catalog，也不构成 runtime implementation、Provider
调用、media proof、P6、Final Acceptance、push 或 release authorization。

## Pre-Implementation Runtime Truth

Current source 已经由 AI-VIDEO 对 fetched bytes 重新计算 SHA、probe 并构造 media/review evidence；
neutral requirement、Gate 1 context 与 Final Acceptance rollup没有把 hidden seed、scheduler、workflow
或 model revision 作为 universal acceptance fields。

仍未实现的目标差异：

- Seedance status/fetch仍强制要求 response `model`；
- MiniMax H3 status/fetch仍强制要求 echoed model、resolution、duration与ratio；
- `provider_file_id`当前serialized bytes不变，但其durable语义需要在implementation中按Spec固定为
  opaque output handle；
- non-requeryable one-shot output URL仍应在`VideoGenerationService.start()`之前由pure sealed
  resolve/compile/preflight拒绝；
- Ecommerce Gate 2相关working-tree文件不是本Spec的accepted implementation truth，本slice也不拥有
  Gate 2、P6或Final Acceptance closure。

## Session Work And Decisions

新增并提交：

```text
docs/superpowers/specs/2026-08-26-ai-video-provider-minimal-evidence-boundary.md
```

Spec固定以下决定：

1. Provider负责submit、status与输出交付；AI-VIDEO负责request/Shot/plan/policy/attempt lineage、
   exact artifact SHA、probe、measurement与acceptance evidence。
2. Provider-native hidden facts在未暴露时保持`UNAVAILABLE`或`UNKNOWN`，不得由requested identity
   伪造actual execution。
3. MVP保留historical `provider_file_id`、observation/fetch/provenance schema与hashes；不为命名澄清
   引入wrapper或Manifest migration。
4. Exact effect ID派生的deterministic handle合法；禁止的是process-local URL cache、raw signed URL
   persistence、无effect lineage的synthetic locator与伪造Provider claim。
5. Signed URL在`REQUERY_BY_EFFECT_ID`策略下允许轮换；`DURABLE_FILE_ID`才要求status/fetch间file ID
   不变。
6. Executable slice止于minimal Provider offline fetch/probe candidate；Gate 2/P6/Final Acceptance E2E
   保持由Quality Gate owner的独立accepted implementation slice验收。

## Implementation Plan Checkpoint

同日新增并提交：

```text
docs/superpowers/plans/2026-08-26-ai-video-provider-minimal-evidence-boundary.md
```

Plan将Spec收敛为五个implementation milestones：pure recovery preflight、Seedance/H3 minimal status、
offline lifecycle到`CANDIDATE`、Gate/T8/compatibility boundary，以及exact-snapshot closure。

Plan self-review纠正了一项重要设计候选：现有`VideoCapabilityVariant.lookup_supported`只能证明
job/status lookup，不能证明output locator可恢复。仅复用它会错误接纳“状态可查询、但URL只返回一次”
的Provider。Accepted implementation direction因此是additive、historical-safe的
`output_recovery_strategy` capability field：

- `DURABLE_FILE_ID`；
- `REQUERY_BY_EFFECT_ID`；
- `NON_RECOVERABLE_EPHEMERAL_URL`。

Historical capability/profile payload缺少该字段时以`None`重开，serializer与canonical fingerprint
projection省略`None`，保留原bytes/hash；但缺少strategy的historical remote profile不得创建new
attempt。Current Seedance/H3应声明`REQUERY_BY_EFFECT_ID`，Hailuo声明`DURABLE_FILE_ID`，Local
T8/ComfyUI保持local-specific `None`。Unsupported或missing remote strategy必须在pure compiler、
`VideoGenerationService.start()`之前返回`OUTPUT_LOCATOR_NOT_RECOVERABLE`。

该Plan不修改observation/fetch/provenance/Manifest schema，不实现Gate 2/P6/Final Acceptance closure，
也不授权Provider、network、credential、ComfyUI或媒体生成。

## Specification And Plan Verification Evidence

- Commit：`5ad0fdd`（`docs: specify provider-minimal evidence boundary`）。
- Exact range：`5ad0fdd^..5ad0fdd`。
- Harness receipt：`.agent/harness/runs/provider-minimal-evidence-spec-20260826/receipt.json`。
- Receipt SHA-256：`8257275747c900495941d03b8c7c2b08f83b65bf8e5293da890d69d58d433750`。
- Harness checks：`scope_diff_check`、`docs_contract_check`、`policy_audit_check`全部PASS。
- Receipt verification：artifact integrity、check completeness、policy/scope/snapshot match、freshness、
  detached worktree cleanliness与cleanup全部为`true`。
- Native `reviewer_xhigh`初审指出Gate 2 scope expansion、handle contract矛盾、preflight位置错误与
  unnecessary schema migration；修订后scoped re-review为`accept`，无blocking或non-blocking concern。

Plan checkpoint evidence：

- Commit：`905c5fa`（`docs: plan provider-minimal evidence implementation`）。
- Exact range：`905c5fa^..905c5fa`。
- Harness receipt：`.agent/harness/runs/provider-minimal-evidence-plan-20260826/receipt.json`。
- Receipt SHA-256：`fc8577fb95b02b9151816111cc47b66018a52b8e19bf563f7128d74ab99f5379`。
- Harness checks：`scope_diff_check`、`docs_contract_check`、`policy_audit_check`全部PASS。
- Receipt verification：artifact integrity、check completeness、policy/scope/snapshot match、freshness、
  detached worktree cleanliness与cleanup全部为`true`。
- Plan placeholder scan、spec-to-plan acceptance mapping与`git diff --check`通过。

Plan的独立review已按repository risk routing发起，但reviewer连续无message/tool-output等可观察进度，
health assessment后被中断；因此不得声称Plan取得independent reviewer verdict。Spec本身先前的accepted
review仍然有效，但不能替代future implementation的required `reviewer_xhigh`。

没有运行runtime/provider test、Provider、network、credential、media generation或human quality
acceptance。本checkpoint只能证明documentation contract及其exact commit-range verification。

## Specification And Plan Publication State

- Spec、Plan与本记录位于local `main`；
- Spec/Plan commits未push、未release；
- existing unrelated staged/dirty/untracked files保持原位，未进入Spec或Plan exact commits；
- Plan checkpoint的Agent Memory retrieval返回stale last-good fragments并queued refresh；Plan没有把这些
  stale fragments当作current source truth，也没有另行刷新index或生成runtime/acceptance authority。

## Offline Implementation Checkpoint

Provider-minimal offline implementation已在以下exact range收敛：

```text
0f73c53..9e999d1
```

Task-owned commits：

- `ab58412 feat: support provider-minimal video recovery`；
- `dc92020 refactor: isolate video capability contract`；
- `5cb65d1 refactor: reuse video capability boundary`；
- `9e999d1 fix: preserve capability serialization order`。

Executable runtime truth：

1. `VideoOutputRecoveryStrategy`由既有`video_contracts.py`边界独占，支持
   `DURABLE_FILE_ID`、`REQUERY_BY_EFFECT_ID`与`NON_RECOVERABLE_EPHEMERAL_URL`。
2. Historical capability payload缺field时以`None`重开；serializer与fingerprint projection省略
   `None`，保持historical bytes/hash与field order。
3. New remote attempt缺少supported strategy或使用one-shot strategy时，pure compiler在
   `VideoGenerationService.start()`前返回`OUTPUT_LOCATOR_NOT_RECOVERABLE`；`lookup_supported=True`
   不能旁路该拒绝，且attempt、Manifest、permit、network与Provider side effects为零。
4. Seedance与MiniMax H3使用`REQUERY_BY_EFFECT_ID`，MiniMax Hailuo使用`DURABLE_FILE_ID`，Local T8
   保持`None`。
5. Seedance/H3 optional Provider echoes缺失时允许继续；冲突echo仍fail closed。H3 output profile echo
   只作advisory，最终SHA/probe以AI-VIDEO local exact bytes为准。
6. Offline fake Provider只返回`job_id + status + re-queryable output_url`，经过neutral requirement、
   Router、compiler、resolve与canonical service到达fetched/probed `CANDIDATE`。重开fresh adapter后按
   effect identity重新查询轮换URL；没有raw signed URL persistence、fallback、blind retry或自动activation。
7. `VideoProvenanceReceipt.model_id/profile_sha256`只表示requested/selected identity，不表示
   Provider-observed actual execution。

Strict RED/GREEN覆盖missing enum、minimal metadata、true restart/re-query、matrix drift、historical reopen、
URL repr、public export、neutral chain与serialization order regression。最终capability-focused复核为
`202 passed`。

Native `reviewer_xhigh`在发现并修复capability serialization field-order regression后，以同tier scoped
re-review给出`Verdict: accept`，无blocking或non-blocking concern。

Exact-range Harness：

- Receipt：`.agent/harness/runs/provider-minimal-evidence-boundary-implementation-20260826-v3/receipt.json`；
- Receipt SHA-256：`c66dad4e3e5c17ca2bac3594b43a74badcca033cd6ff6f2e148c87862072a36e`；
- `production_review_tests`：`636 passed`；
- `production_video_provider_tests`：`696 passed`；
- `provider_neutral_video_requirement_tests`：`300 passed`；
- Architecture Gate：PASS；
- integrity、freshness、fresh-for-snapshot、snapshot、policy、scope、cleanup、closure与overall passed均为
  `true`。

## Implementation Publication State

- Implementation commits与本checkpoint均只在local `main`；未push、未release。
- 没有调用Provider、network、credential、ComfyUI，也没有生成媒体。
- unrelated staged/dirty/untracked work保持原位，未进入exact implementation range或detached Harness
  execution tree。

## Canonical Closure Checkpoint

先前same-file owner完成并提交其独立工作后，canonical files变为clean；本task随后完成Milestone 5同步：

- Commit：`2c2ee07`（`docs: close provider-minimal evidence boundary`）；
- 更新`docs/agent-primary-contract-matrix.md`，固定output recovery、optional echo、local probe与
  requested/selected provenance的single-owner/forbidden-bypass/focused-verification contract；
- 更新`docs/v0.2-runtime-baseline.md`，只声明offline minimal response到未激活`CANDIDATE`的current
  runtime truth；
- 更新`docs/v0.2-agentic-production-roadmap.md`，记录该slice complete以及live/media/Gate 2/P6/Final
  Acceptance仍未验证；
- 更新Spec与Plan Status为offline complete；
- `.agent/harness/policy.yaml`未修改，因为current implementation paths已全部由existing
  `production_video_provider`与`provider_neutral_video_requirement`categories覆盖，implementation receipt
  没有unmapped或fallback path。

Canonical documentation exact-range Harness：

- Receipt：`.agent/harness/runs/provider-minimal-evidence-boundary-canonical-closure-20260826/receipt.json`；
- Receipt SHA-256：`28dd38d3294d6ab150de074ed9c9a647dcd86cecbf40ff1fd1d33f4c0a954a86`；
- `harness_tests`：`185 passed`；
- Documentation Contract Gate与policy audit：PASS，无missing、unmapped、unreferenced或unverified paths；
- integrity、freshness、fresh-for-snapshot、snapshot、policy、scope、cleanup、closure与overall passed均为
  `true`。

## Remaining Risks Or Next Work

- Live Provider API grammar、account、network、billing、real media、model quality与human visual verdict均
  未验证。
- Gate 2、P6与Final Acceptance closure仍属于Quality Gate owner的独立slice；validated `CANDIDATE`
  不等于activation或acceptance。

## Agent Guardrails

- 不得把`VideoProvenanceReceipt.model_id`解释为Provider-observed actual model；
- 不得因Provider缺少hidden metadata而伪造seed、scheduler、revision或workflow；
- 不得用Provider response output profile替代local artifact probe；
- 不得为支持one-shot URL使用process-local cache、raw URL persistence或blind retry；
- 不得把本Spec的documentation PASS描述成runtime、live、quality、P6或Final Acceptance PASS。
