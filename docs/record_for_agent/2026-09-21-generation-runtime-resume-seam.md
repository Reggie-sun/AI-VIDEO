# Generation Runtime-Resume Seam Record

Date: 2026-09-21

---
record_kind: architecture_implementation
topic_id: generation-runtime-resume-seam
learning_eligibility: eligible
evidence_index_version: "1"
---

## Purpose

记录并固化一次契约级死锁(root cause + T3 修复):local runtime failure 被真实评估后,v0.2 Production Harness 的决策层永久锁死该 Shot 的重新生成,且不存在契约内恢复路径(catch-22)。修复以最小 additive seam 授权"显式修复环境后的一次有界重执行"。

## Current Runtime Truth

- 死锁组合(修复前):
  1. `ProductionStateCommitter._require_submit_execution_binding`(`src/ai_video/production/_state_commit_video.py`)要求 FAILED 的 prior attempt 必须已持久化 `runtime_failure` 评估证据,否则拒绝下一 attempt 的 submit。
  2. `resolve_generation_decision`(`src/ai_video/production/generation_decision.py`)的 blocking loop 在 shot 级 `latest` 证据为 `runtime_failure` 时永久返回 `RUNTIME_FAILURE` disposition。`latest` 按 shot 维度取值(task_id 只隔离 submit 配额),intervention、`abandoned_result`、`goal_changed` 均不可绕过;FAILED attempt 在 `video_resume_next_action` 下也是 terminal "stop"。
  3. 实测命中:`runs/ninebot-n3-lighting-ad-20260920-001` 的 `attempt-shot-intro-5` 因 VRAM OOM 失败(ComfyUI VRAM grow 需 778520576 bytes、仅 ~498MB 可用;同机 llama-server pid 3248274 以 `--n-gpu-layers 99` 持有 ~25942 MiB / 32607 MiB)。评估被真实记录后,shot-intro 在此 run 内无法再生成——任何换 task_id、换 Provider、重驱 binding 的尝试都被同一 planner 锁死。
- 修复(本记录对应实现,T3,用户 2026-09-21 明确授权 "授权 T3 修复(推荐)"):
  - 新 artifact `RuntimeRepairAuthorization`(schema `runtime-repair/1`,`src/ai_video/production/generation_runtime_repair.py`),immutable、content_hash 自校验;`ProductionStateCommitter.record_runtime_repair_authorization` 是唯一写入口(要求 attempt FAILED + 最新 experience 含 `runtime_failure` 证据;per-shot 上限 `MAX_RUNTIME_REPAIRS_PER_SHOT = 2`;同 evidence_hash 幂等返回既有 pointer)。
  - `VideoGenerationAttemptState.runtime_repairs` additive 字段(`src/ai_video/production/_lifecycle_schema.py`),serializer 空值弹出,旧 manifest 兼容。
  - planner 分支:`diagnosis.failure_classes == ("RUNTIME_FAILURE",)` 且存在 `not consumed && evidence_hash == latest.evidence_hash && attempt_id == latest.attempt_id` 的 grant 时,选中 `scope_hash == latest.recipe_scope_hash` 的 candidate(不存在则 `EVIDENCE_GAP`),豁免 fit 门槛,跳过 RUNTIME_FAILURE block,`decision.runtime_repair` 携带 authorization。质量 findings、unknown_outcome、混合 failure class、无 grant/错配/consumed 一律维持原阻断行为。
  - 一次性消费:`record_local_video_submit_intent` 的 exclusive-lock 原子写内校验 pointer 未消费 + content_hash 精确匹配 + reopen 一致,随后在同一 manifest write 中标记 `consumed=True`;paid submit 路径显式拒绝消费 runtime repair grant(fail closed)。
  - 运行期接线:`runs/ninebot-n3-lighting-ad-20260920-001/live_driver.py` `stage_shot_fetch` 在重建 shot plan 前,对 `attempt-shot-intro-5` 幂等记录 runtime repair authorization(修复事实:co-tenant 已停、VRAM 已释放)。该文件属 `.gitignore` 的 `runs/*`,不纳入 git,留作运行期 glue。
- 设计 spec(accepted contract):`docs/superpowers/specs/2026-09-21-generation-runtime-resume-seam.md`。

## Session Work And Decisions

- root cause 定位:逐一验证所有逃逸路径均闭合(intervention 需 QUALITY_FAILURE、abandonment 仅媒体质量、`video_resume_next_action` FAILED→stop、binding 重驱被 stale-evidence check 阻断、paid lane 同一 planner),确认是 guard 组合缺口而非配置问题;既有测试只覆盖 block 本身,从未覆盖 block 之后的恢复。
- 用户裁决选项:报告 catch-22 后,用户选择 "授权 T3 修复(推荐)"(备选为放弃 shot-intro 或改走 paid Provider;均会牺牲已冻结的 local-first 契约或成片目标)。
- 实现保持 additive:不改既有 disposition 语义、不放宽 fail-closed、不引入第二套 lifecycle truth;mutable lifecycle(consumed)只存于 canonical Manifest owner。
- runtime repair 的 compiled request 与失败 attempt 相差 paired seed(+1)——规划器标准配对进展(`create_generation_candidates` baseline 匹配时 seed+1),`scope_hash` 使用 `fit_hash`(排除 seed/comparison)故精确匹配成立;声明变量仍为环境修复,非质量下注。

## Verification And Evidence

- 新测试 `tests/test_generation_runtime_repair.py`(10 个,全部通过):planner 侧:无 grant 阻断、grant 授权精确重执行(GENERATE_ONCE + candidate 匹配 + intervention 为 None)、consumed/错配 evidence_hash/错配 attempt_id 仍阻断、receipt content_hash 自校验防篡改;committer 侧:非 FAILED 拒绝、无 runtime_failure 证据拒绝、幂等重记录(manifest revision 不变)、一次性消费后 pointer.consumed=True 且再次 prepare 回到 RUNTIME_FAILURE、per-shot 预算耗尽拒绝。
- 回归:decision / feedback review / execution / local-video state / quality rejection / paid submit quota / no-effect reconciliation / historical replay 共 8 个套件 165 个测试通过;schema 往返(`test_production_models.py`、`test_generation_history_import_receipt.py`)305 个测试通过。
- 记录时状态:实现 + 测试已 staged(9 个 task-owned 路径,dual independent review 进行中);`live_driver.py` 的运行期 glue 为 working-tree 修改(`.gitignore` 内),不纳入 commit;attempt-6 重跑(shot-intro 重新生成)尚待在 review 裁决与 harness verify 后执行。
- 本记录不声明 attempt-6 已生成或 shot-intro 已恢复;那是下一稳定边界的事实。

## Evidence Index

```text
evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source
ev-oom-1 | ninebot-shot-intro-oom-20260921 | ninebot-n3-lighting-ad-20260920-001 | attempt-shot-intro-5 | NONE | NONE | technical | FAIL | RUNTIME_FAILURE | primary | N/A | runs/ninebot-n3-lighting-ad-20260920-001 state manifest + ComfyUI VRAM grow failure observation (778520576 bytes requested, ~498MB free; co-tenant llama-server pid 3248274 held ~25942 MiB of 32607 MiB, stopped 2026-09-21)
ev-fix-2 | runtime-resume-seam-impl-20260921 | generation-runtime-resume-seam | N/A | N/A | N/A | technical | PASS | N/A | implements | ev-oom-1 | tests/test_generation_runtime_repair.py (10 tests) + 165-test regression across decision/feedback/execution/local-video/rejection/paid-quota/no-effect-replay/historical-replay suites
ev-fix-3 | runtime-resume-seam-impl-20260921 | generation-runtime-resume-seam | N/A | N/A | N/A | technical | PASS | N/A | implements | ev-oom-1 | docs/superpowers/specs/2026-09-21-generation-runtime-resume-seam.md (accepted T3 contract)
```

## Assessment

- 这是契约缺口,不是媒体质量问题:单项 guard 各自正确,组合后无恢复路径。修复以 "显式授权 + 一次性消费 + per-shot 预算" 保持 fail-closed,而非放宽阻断。
- 与 empirical 规则的关系:本次修复不涉及媒体能力实验;trigger 是确定性契约死锁 + 用户显式授权,符合 Empirical Validation Priority 的 pure deterministic 排除项。
- 成片目标优先原则:不修复则 shot-intro 无法生成,广告成片缺失开场镜头,任务无法交付;修复是满足当前交付目标的最小可执行路径。

## Remaining Risks Or Next Work

- dual review 结论未落地;如有 blocking finding,修复后生成新 review target 重审,再 path-limited commit + detached worktree harness verify。
- attempt-6 重跑、Per-Shot Gate(含 h3-i2v first-frame conditioning head continuity 的 dark ff-hook head 验证)、shot-validate 激活、compose → review → deliver 均尚待执行。
- runtime repair 不消费质量干预预算、不推进 activation/QA;attempt-6 生成后仍需走完整 Per-Shot Gate 与验收链。
- 未验证区域:paid Provider 路径与 runtime repair 的交互按 fail-closed 拒绝处理,无 live 证据(设计如此,超出本 seam 范围)。

## Agent Guardrails

- `record_runtime_repair_authorization` 是唯一写入口;不得 hand-mut manifest 的 `runtime_repairs`。
- grant 消费必须与 replacement submit intent 同一原子写;不得事后补标 consumed。
- mixed failure class(如 runtime + 质量 findings)永远阻断,不得用 runtime repair 绕过质量 Gate。
- 每 Shot 上限 2;耗尽后必须停止并报告,不得换 attempt_id/task_id 重铸 grant。
- 本记录的测试/回归证据是离线确定性证据;不授权 paid/live 调用。