# Provider-Minimal Evidence Boundary Specification Record

Date: 2026-08-26

## Purpose

本文记录 `docs/superpowers/specs/2026-08-26-ai-video-provider-minimal-evidence-boundary.md`
达到稳定 documentation checkpoint 时的 verified scope、关键架构决定与证据边界。详细 contract
以该 Spec 为唯一 owner；本记录不复制字段 catalog，也不构成 runtime implementation、Provider
调用、media proof、P6、Final Acceptance、push 或 release authorization。

## Current Runtime Truth

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

## Verification And Evidence

- Commit：`5ad0fdd`（`docs: specify provider-minimal evidence boundary`）。
- Exact range：`5ad0fdd^..5ad0fdd`。
- Harness receipt：`.agent/harness/runs/provider-minimal-evidence-spec-20260826/receipt.json`。
- Receipt SHA-256：`8257275747c900495941d03b8c7c2b08f83b65bf8e5293da890d69d58d433750`。
- Harness checks：`scope_diff_check`、`docs_contract_check`、`policy_audit_check`全部PASS。
- Receipt verification：artifact integrity、check completeness、policy/scope/snapshot match、freshness、
  detached worktree cleanliness与cleanup全部为`true`。
- Native `reviewer_xhigh`初审指出Gate 2 scope expansion、handle contract矛盾、preflight位置错误与
  unnecessary schema migration；修订后scoped re-review为`accept`，无blocking或non-blocking concern。

没有运行runtime/provider test、Provider、network、credential、media generation或human quality
acceptance。本checkpoint只能证明documentation contract及其exact commit-range verification。

## Publication State

- Spec与本记录位于local `main`；
- Spec commit未push、未release；
- unrelated dirty/untracked files保持未修改、未stage、未commit；
- Agent Memory retrieval使用fresh local advisory index，没有生成runtime或acceptance authority。

## Remaining Risks Or Next Work

- Seedance与MiniMax H3 adapter coupling仍存在于current code；
- output recovery guarantee尚未进入selected sealed pre-start evidence；
- minimal response fake Provider offline E2E、historical hash compatibility与old-path retirement tests尚未实现；
- live Provider、paid/cloud、media quality、Gate 2/P6/Final Acceptance evidence均未执行。

后续implementation必须以Spec的Acceptance Criteria为准，并在任何Provider effect前保持Paid Provider
Gate、unknown-outcome、no-fallback、single committer与explicit recovery contract。

## Agent Guardrails

- 不得把`VideoProvenanceReceipt.model_id`解释为Provider-observed actual model；
- 不得因Provider缺少hidden metadata而伪造seed、scheduler、revision或workflow；
- 不得用Provider response output profile替代local artifact probe；
- 不得为支持one-shot URL使用process-local cache、raw URL persistence或blind retry；
- 不得把本Spec的documentation PASS描述成runtime、live、quality、P6或Final Acceptance PASS。
