# Continuity Review Coordinator And Human Evidence UI Plan

## Status

Ready for bounded implementation。当前优先完成 Product caller 与 exact-bound human decision
闭环；随后单独完成只读 Human Evidence UI。Manifest `HUMAN_PENDING`、后台 scheduler、多人队列与
automatic measurement overlay 明确延后，只有满足本文的升级条件时才进入新的 schema/lifecycle slice。

本计划不恢复 `.agent/context/session-handoff.md` 中的 rough-cut 媒体生产，不执行 live/paid
Provider、媒体生成或质量验收。

## Goal

把已经存在的 local CUDA continuity reviewer 接入一个明确、可重放、local/no-network 的产品调用路径：

1. fetched video attempt 到达 `VALIDATE` 后，生成与 exact attempt/artifact/request/policy 绑定的
   human review request；
2. 人工通过只读 UI 对七个 continuity 维度作出 decision；
3. Product caller 校验 decision、显式组装 reviewer，并调用现有
   `VideoGenerationService.fetch_and_activate(...)`；
4. automatic evaluator 只产生 measurements/evidence，最终 verdict 继续由现有 P6 adjudicator 派生；
5. 只有 `ProductionStateCommitter` 可以持久化 evidence、candidate 与 activation。

## Problem Boundary

- **Single product orchestration owner:** 新的 Production-side
  `ContinuityReviewCoordinator`。它是 explicit one-shot caller，不是 daemon、目录 watcher 或常驻 queue
  worker。
- **Single durable writer:** `ProductionStateCommitter`，保持不变。
- **Single verdict owner:** `adjudicate_generated_shot_continuity()` / P6，保持不变。
- **Human UI owner:** Provider Console 的 read-only projection + decision authoring surface；它不写
  Manifest，不创建 canonical evidence，不触发 activation。
- **Existing execution seam:** `VideoGenerationService.fetch_and_activate(...,
  continuity_reviewer=...)` 与 `create_local_cuda_continuity_reviewer(...)`。
- **Old path to replace:** 手工 Python 组装 callback、临时 decision glue 或依赖测试才能触发 reviewer 的路径。
  不新增第二条 activation path。

## Unchanged Contracts

- automatic model 不得自报 PASS；P6 是唯一 verdict authority。
- automatic mismatch 立即 fail closed，human decision 不得覆盖或改写为 PASS。
- identity、camera axis、framing 或其他无法可信自动判定的维度保持 `NOT_EVALUATED`，只能由 exact-bound
  human evidence 补齐。
- 缺 reviewer、缺 decision、`NOT_SURE`、binding 不一致、低 coverage 或低 confidence 均停在
  `VALIDATE`；不得猜测通过或自动 activation。
- exact replay 不重复 evaluator、human fallback、Provider、renderer 或 Manifest side effect。
- Provider Console 保持 GET/read-only；不新增 evidence POST endpoint。
- 不新增 dependency、remote Provider、credential path、MCP runtime coupling 或 cloud egress。
- 人工等待不得发生在 committer exclusive lock 内，也不得占用 GPU。

## Trigger Contract

### Review Request Trigger

只在以下条件同时满足时允许 `prepare_request(attempt_id)`：

- attempt 已完成 FETCH 且当前 durable phase 为 `VALIDATE`；
- 当前 request 包含 continuity binding；
- exact fetched artifact、resolved request、continuity constraints 与 QA policy 均可重新打开并验证；
- 当前 attempt 尚无可重放的 continuity evidence。

该调用是 read-only，不运行 CUDA evaluator，也不推进 Manifest phase。

### Automatic Evaluator Trigger

CUDA evaluator 不是“一定触发”。它只在用户或产品显式调用
`validate_and_activate(attempt_id, decision_path)`，且以下条件成立时触发一次：

- attempt 仍处于相同的 `VALIDATE` 状态；
- decision 与当前 review request exact binding 一致；
- 没有已持久化、可重放的 continuity evidence；
- 本地 GPU execution preflight 允许启动，并且产品调用方没有 active ComfyUI generation job；
- sealed model/profile/ffmpeg contract 仍有效。

若 evidence 已存在，replay 必须 reopen evidence，不再调用 evaluator。无 continuity binding 的 Shot 不进入
该 reviewer。

### Human Fallback Trigger

human fallback 也不是“一定触发”。只有 automatic measurements 没有明确 mismatch、但至少一个维度仍为
`NOT_EVALUATED` 时，才消费已校验的 human decision。automatic mismatch 必须绕过 human fallback，并由
P6 派生 FAIL。

## Phase 1 — Product Caller And Bound Decision

### Proposed Change Surface

Create：

- `src/ai_video/production/continuity_review_coordinator.py`
- `tests/test_production_continuity_review_coordinator.py`

仅在 executable tests 证明现有 seam 不足时，才修改：

- `src/ai_video/production/video_generation.py`
- `src/ai_video/production/video_artifact.py`
- `src/ai_video/production/review.py`
- `src/ai_video/production/local_continuity_reviewer.py`

默认不修改 Manifest schema、committer lifecycle 或 Provider Console。

### Coordinator API

```python
class ContinuityReviewCoordinator:
    def prepare_request(self, *, attempt_id: str) -> HumanReviewRequestV1: ...

    def validate_and_activate(
        self,
        *,
        attempt_id: str,
        decision_path: Path,
    ) -> object: ...
```

`prepare_request()` 只产生 projection。`validate_and_activate()` 必须重新打开 canonical state，拒绝 stale
decision，构造 file-bound `HumanContinuityFallback`，再显式调用现有
`fetch_and_activate(..., continuity_reviewer=reviewer)`。Coordinator 不直接写 Manifest，也不直接调用
activation committer method。

### HumanReviewRequestV1

review request 至少绑定：

- `attempt_id`
- `source_shot_id`
- `target_shot_id`
- `target_shot_content_hash`
- `resolved_generation_hash`
- `artifact_sha256`
- `continuity_constraints_hash`
- `qa_policy_content_hash`
- reviewer policy/identity requirement
- exact media token 或等价的 path-safe projection identity
- canonical `content_hash`

所有字段由 canonical reader 派生，不允许 UI 编辑。request 是 read-only projection，不是第二套 lifecycle
state。

### HumanReviewDecisionV1

decision 至少包含：

- `review_request_content_hash`
- nonblank、policy-accepted reviewer identity
- 七项 `PASS | FAIL | NOT_SURE`
- nonblank `rationale`
- canonical `content_hash`

七项为：identity、camera axis、framing、motion direction、entrance、exit、unexpected re-entry。
`NOT_SURE` 不能转换为 boolean PASS，必须阻止完整 evidence 形成并保持 `VALIDATE`。

decision 文件不是 canonical `GeneratedShotContinuityEvidence`。fallback 被调用时，必须使用 runtime 传入的
exact request、measured artifact 与 QA policy 补全 canonical binding；decision 只能提供人工结论与
rationale。

### GPU Scheduling

- Product caller 只在 explicit `validate_and_activate()` 时申请 evaluator execution。
- Human review 阶段不启动 CUDA session。
- 初始实现采用 generation/reviewer 串行策略；有 active ComfyUI generation 时 fail closed 为 typed busy/
  unavailable result，不并发争抢显存。
- 不承诺 active H3 inference 与 continuity evaluator 同时运行；已有显存观察只能证明 resident/idle
  coexistence，不是 active concurrency acceptance。
- GPU availability seam 必须 local、injectable、可测试；不得因此新增网络、dependency 或后台 scheduler。

### Phase 1 Regression Tests

必须覆盖：

- review request 与 exact attempt/artifact/request/constraints/policy binding；
- stale artifact、stale policy、wrong attempt 与 tampered content hash 被拒绝；
- reviewer identity missing/blank 被拒绝；
- automatic direction reversal、exit mismatch、unexpected re-entry 不能被 human decision 覆盖；
- identity/axis/framing incomplete 时消费 exact-bound human decision；
- 任一 `NOT_SURE` 保持 human fallback incomplete，不能 activation；
- automatic mismatch 时 human fallback 调用次数为零；
- evidence replay 时 evaluator 与 human fallback 调用次数均为零；
- missing decision、GPU busy、invalid sealed runtime 均 fail closed 且无 Manifest advancement；
- coordinator 不直接执行 committer write 或 activation side effect。

Focused verification：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_continuity_review_coordinator.py \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_local_continuity_reviewer.py \
  tests/test_production_video.py \
  tests/test_production_video_state_recovery.py -q
```

## Phase 2 — Read-Only Human Evidence UI

Phase 1 通过并 commit 后再开始，作为独立 staged snapshot 与 commit。

### UI Responsibilities

- 展示 exact fetched MP4、source/target Shot、continuity constraints 与七个维度；
- hashes 默认可折叠，但必须只读可查看；
- 每个维度提供 `PASS / FAIL / NOT_SURE`；
- `Unexpected re-entry` 使用“是否出现不符合约束的重新入画”文案，避免正负逻辑反转；
- `rationale` 必填，reviewer identity 来自可信 local configuration，不允许表单任意伪造；
- 只导出 `HumanReviewDecisionV1`，按钮文案不得暗示“Approve activation”。

### UI Boundaries

- Provider Console bridge 继续只提供 GET/read-only projection 和 media；
- 不新增 `POST /continuity-evidence`、Manifest write、committer import 或 Provider call；
- MVP 不展示 automatic detector box、track 或 raw measurement overlay，因为 evaluator 尚未运行；
- UI export success 不等于 evidence accepted、P6 PASS 或 candidate activation。

### Phase 2 Verification

- Python projection tests：binding、path containment、media token、sanitization、zero writes；
- Node tests：GET-only、405、tampered request/decision rejection、no-store；
- React tests/build：七项输入、`NOT_SURE`、rationale、locked bindings、export payload；
- Chrome integrated QA：真实 local attempt、video playback、keyboard accessibility、empty/stale/error states；
- `runs/**` 与 Manifest pre/post snapshot 必须无 UI-side write。

## Deferred Phase — HUMAN_PENDING And Async Queue

只有出现以下至少一个已确认产品需求时，才起草独立 spec/plan 并请求 schema/lifecycle approval：

- 多人领取、排队或转交 review；
- UI 必须先展示已执行的 automatic measurements/track overlays；
- Manifest 必须 canonical 地区分普通 `VALIDATE` 与“等待人工”；
- review 需要跨机器、服务端提交、账户认证或长期 audit queue；
- human turnaround 需要 durable pending/recovery，而不是本地 immutable decision file。

届时才考虑 `VALIDATE -> HUMAN_PENDING -> EVIDENCED -> P6` 与唯一 committer action，例如
`record_human_continuity_evidence()`。不得通过 Console 直接写 Manifest 实现该功能。

## Acceptance Criteria

- 产品有唯一、显式、one-shot 的 reviewer caller；不存在后台自动扫描或第二条 activation path。
- Human decision 与 exact artifact/request/policy/attempt content hash 绑定，stale/tampered decision fail closed。
- automatic mismatch 不可由人工覆盖；semantic uncertainty 只能由 human evidence 补齐。
- P6 与 `ProductionStateCommitter` 的既有 ownership 未改变。
- replay 不重复 evaluator 或 human side effect。
- ComfyUI active generation 与 evaluator 默认串行；未验证 active concurrency 时不作显存充分声明。
- Console 保持 read-only，UI 不产生 canonical evidence 或 activation verdict。
- 所有 task-owned changes 按 `.agent/harness/policy.yaml` 对 exact staged snapshot 验证并分别 commit。
- 未执行 real Shot calibration、active ComfyUI concurrency、媒体生成或 Final Acceptance 时必须明确报告。

## Rollback

Phase 1 可通过删除 coordinator/decision module 与 focused tests 回滚；existing reviewer、P6、committer 与
Manifest 不变。Phase 2 可独立恢复 Provider Console projection/UI files；不得删除 `runs/**`、evidence、
Harness receipt 或其他 concurrent work。
