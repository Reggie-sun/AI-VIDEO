# Generation Runtime-Resume Seam Specification

## Status

Approved T3 contract change（用户 2026-09-21 明确授权）。修复 local runtime failure 之后
canonical 决策层永久锁死 Shot 生成的组合缺口（catch-22）。

## Context

v0.2 Production Harness 的 fail-closed 守卫在以下组合下形成死锁（2026-09-21
ninebot-n3-lighting-ad run 实际命中）：

1. `ProductionStateCommitter._require_submit_execution_binding`
   （`src/ai_video/production/_state_commit_video.py:235-247`）要求 FAILED 的 prior
   attempt 必须已持久化 `runtime_failure` 评估证据，否则拒绝下一 attempt 的 submit。
2. `resolve_generation_decision`
   （`src/ai_video/production/generation_decision.py:422-429`）在 shot 级 `latest`
   证据为 `runtime_failure` 时永久返回 `RUNTIME_FAILURE` disposition，拒绝规划任何
   新生成。`latest` 按 shot 维度取值（task_id 只隔离 submit 配额），intervention、
   `abandoned_result`、`goal_changed` 均不可绕过。

后果：一旦本地 attempt 因运行时原因（如 VRAM OOM）失败且评估被真实记录，该 Shot 在此
run 内无法再生成；同 submit 守卫又强制要求该评估存在。换 Provider/换 task/重驱同一
attempt 均无契约内路径。测试只覆盖了 block 本身，从未覆盖 block 之后的恢复。

## Goals

- local runtime failure（纯运行时失败，无质量 findings）经显式修复后，决策层可以授权
  **一次有界重执行**，使 Shot 恢复可生成。
- 不放宽任何现有 fail-closed 语义：`unknown_outcome` 仍阻断；混合 failure class 仍阻断；
  runtime repair 不消费质量干预预算；不自动推进 activation/QA。
- 全部授权走 durable receipt + committer 唯一写入口；决策层只读消费。

## Non-Goals

- 不支持质量失败（QUALITY_FAILURE）的 resume；质量修复仍走 intervention/abandonment。
- 不支持跨 Shot、跨 run、跨 Provider 的 runtime repair。
- 不改变 submit 配额语义（runtime repair 的 submit 在其自身 task_id 下正常计数）。
- 不修改 Legacy 0.1.x 路径。

## Architecture

```text
operator/agent (runtime_owner)
  -> ProductionStateCommitter.record_runtime_repair_authorization  # 唯一写入口
       - 校验: attempt FAILED; 其最新 experience 为 runtime_failure;
         每 Shot 上限 MAX_RUNTIME_REPAIRS_PER_SHOT=2; 同一 evidence_hash 只允许一次
       - 写 immutable artifact state/video-generation/runtime-repair/<hash>.json
       - manifest attempt state 注册 pointer(consumed=False)
  -> GenerationFeedbackOrchestrator.prepare
       - history() reopen 全部 runtime_repair authorizations -> DecisionInputs.runtime_repairs
       - resolver: latest 诊断恰为 ("RUNTIME_FAILURE",) 且存在匹配未消费 authorization
         -> GENERATE_ONCE, selected = 与失败 recipe_scope_hash 一致的 candidate
         -> decision.runtime_repair = 该 authorization
  -> submit (record_local_video_submit_intent, 同一 atomic write)
       - 校验 decision.runtime_repair: pointer 存在、未消费、evidence_hash/attempt_id 精确匹配
       - 标记 consumed=True; 之后同一 authorization 不可复用
```

## Contracts

### RuntimeRepairAuthorization（新 artifact，schema "runtime-repair/1"）

字段：`schema_version, attempt_id, evidence_hash`（被修复的 runtime_failure 证据）
`repair_basis`（运行时类别与修复事实，min_length=1）、`actor: ActorIdentity`、
`expected_manifest_revision`（informational：记录授权时 committer 看到的 manifest
revision，用于 audit traceback；消费时 committer 不做严格比对，因为 manifest revision
会随其他 reader/comitter 写入而单调递增，binding 阶段已捕获 decision 的 sealed 视角）、
`content_hash`（自校验）。

不变量：artifact immutable；`content_hash = canonical_sha256(model_dump)`；pointer 存于
`VideoGenerationAttemptState.runtime_repairs: tuple[Pointer, ...] = ()`（additive
optional，空时 serializer 弹出，旧 manifest 兼容）。

### 决策层（generation_decision.py）

- `DecisionInputs.runtime_repairs: tuple[RuntimeRepairAuthorization, ...] = ()`（additive）。
- `GenerationDecision.runtime_repair: RuntimeRepairAuthorization | None = None`（additive）。
- `resolve_generation_decision`：在 goal_changed rubric 检查之后、blocking loop 之前，
  若 `diagnosis.failure_classes == ("RUNTIME_FAILURE",)` 且存在
  `not consumed && evidence_hash == latest.evidence_hash && attempt_id == latest.attempt_id`
  的 authorization：选中 `scope_hash == latest.recipe_scope_hash` 的 candidate
  （不存在则 EVIDENCE_GAP），走既有 GENERATE_ONCE tail；eligible 过滤对 repair candidate
  豁免 fit 门槛（runtime repair 不是质量下注）；`decision.runtime_repair` 携帯该
  authorization。其余路径（混合 class、unknown_outcome、无 authorization）行为不变。

### Committer（_state_commit_video.py）

- `record_runtime_repair_authorization(*, attempt_id, repair_basis, actor, evidence_hash=None)`
  ：evidence_hash 默认取该 attempt 最新 runtime_failure 证据；幂等（同 evidence_hash
  已存在则返回既有 pointer）；上限校验按 shot（经 attempt request 的
  activation_scope.target_shot_id 统计同 shot 全部 attempt 的 authorization 数）。
- `record_local_video_submit_intent`：binding.decision.runtime_repair 非空时，于同一
  exclusive-lock 写内校验（未消费、精确匹配）并标记 consumed。

## Verification

- 新增单测：
  - planner：runtime_failure latest 无 authorization → 仍 RUNTIME_FAILURE；
    有未消费 authorization → GENERATE_ONCE 且 candidate 匹配失败 recipe；
    consumed/错配 evidence/混合 failure class → 仍阻断；
  - committer：非 FAILED attempt 拒绝；同 evidence 幂等；per-shot 上限；submit 消费
    后不可复用（第二次 submit 引用同一 authorization 被拒）。
  - 既有测试全量回归（generation decision / guards / feedback / state commit）。
- 验收：ninebot run attempt-6 走 runtime repair 完成 submit → 生成 → Per-Shot Gate →
  compose → deliver。

## Risks

- additive manifest 字段在旧 reader 上的兼容性：serializer 空值弹出 + 默认值 ()，现有
  round-trip 测试应无感；若 schema_version 断言测试失败，再评估 bump 2.2。
- runtime repair 的 compiled request 与失败 attempt 相差 paired seed(+1)（规划器标准
  配对进展），声明变量仍为环境修复；在 rationale 与 receipt 中如实记录。
