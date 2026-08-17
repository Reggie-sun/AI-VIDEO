# Task 10 Report

## Status

DONE — P7 image generation 现在具备 fail-closed crash recovery、精确成功重放与 image-specific outcome-unknown 语义；本任务未执行 merge、push、release、网络访问或真实 Provider 调用。

## Implementation

- 新增 `_StateCommitImageRecoveryMixin`，让 `ProductionStateCommitter.recover()` 成为 P7 image attempt 的唯一 recovery owner：
  - `request` 阶段恢复为 `INTERRUPTED`；
  - submit/provider/materialize/validate 的不完整结果恢复为 `OUTCOME_UNKNOWN`，错误码为 `IMAGE_PROVIDER_OUTCOME_UNKNOWN`；
  - 完整 candidate 只接受 exact old `(project, registry, graph)` 或 exact new tuple，拒绝 mixed tuple；
  - old tuple 保留 authoritative eight-artifact evidence 并标记 interrupted，new tuple 经 standard loader 重验后收敛为 succeeded。
- 抽取并复用 `verify_image_attempt_evidence()`，统一重开和验证 request、result、receipt、PNG、Shot、Project、Registry、Dependency Graph 八项权威证据及聚合 hash。
- `generate_image_asset()` 在任何 durable write、permit、Provider 或 candidate preparer 之前执行 exact replay：仅当已成功 attempt、active tuple、request/preview/authorization、八项证据与 dependency state 均完全一致时返回；同 request 的 unresolved、terminal non-success 或篡改证据均 fail closed。
- 增加 image lifecycle crash checkpoints，覆盖 permit consumption、Provider result、candidate Manifest replace/reopen 与 final Manifest replace/reopen。
- recovery 保留 Manifest 2.5 的 P6 QA/review/repair/final-acceptance fields 与 stale render state，并通过 standard loader 重验 active P7 bundle。
- temp cleanup 仅清理 image attempt 所有的 `.p2a-<attempt>-*.tmp` 与 reserved `state/images/requests` 直接命名空间中的未记录 request temp。

## TDD Evidence

先观察到以下 RED，再实施最小修复：

- exact replay 第二次调用在 `begin_image_generation()` 被 stale-base 拒绝，证明 replay 尚未位于首写之前；
- Manifest 2.5 inactive candidate recovery 落入 P5 incomplete identity 错误，证明没有 P7 recovery owner；
- active request evidence 被篡改时 recovery 未拒绝；
- R+1 crash 后 `.p2a-image-attempt-1-*.json.tmp` 未被 recovery 清理。

修复后新增/扩展测试覆盖：exact replay zero Provider/preparer/Manifest writes、tampered replay fail closed、old/new/mixed tuple recovery、active/inactive evidence tamper、same-request no-resubmit、P6+P7 retained state、7 个 image-specific subprocess checkpoints、45 个 artifact byte-window checkpoints、16 个 Manifest byte-window checkpoints、重复 recovery 幂等与 temp cleanup。

## Verification

- Required P7/P6 suite:
  - `python -m pytest -p no:cacheprovider tests/test_production_state_recovery.py tests/test_production_state_commit.py tests/test_production_image_e2e.py tests/test_production_review.py tests/test_production_repair.py -q`
  - Result: `476 passed in 181.70s`
- Structure and standard loader suite:
  - `python -m pytest -p no:cacheprovider tests/test_production_state_commit_structure.py tests/test_production_project.py -q`
  - Result: `157 passed in 13.30s`
- `python -m scripts.architecture_gate check`
  - Result: PASS, `0` errors；仅保留已有 `src/ai_video/production/image.py +27 LOC` warning，本任务未修改该文件。
- `git diff 6001879 -- src/ai_video/production/dependency.py`
  - Result: empty。
- `git diff --check`
  - Result: clean。
- `python -m compileall -q src/ai_video/production tests/helpers/p2a_crash_worker.py tests/test_production_state_recovery.py tests/test_production_state_commit.py`
  - Result: passed。

## Safety And Scope

- 未修改 `dependency.py`、public exports、CLI、schema/model 定义或 Task 9B 文件。
- recovery 路径不创建 permit，不调用 Provider，不调用 candidate preparer。
- 测试只使用 deterministic fake Provider/preparer；没有真实外部调用。
- 未 merge、push 或 release。

## Self Review

- recovery 只在 standard loader 与 authoritative eight-artifact proof 成功后接受 active new tuple。
- exact replay 在首个 durable write 前完成，且重放路径不会推进 Manifest revision。
- mixed tuple、非唯一同 fingerprint attempt、terminal non-success 与 evidence tamper 均拒绝 blind retry。
- temp cleanup 使用精确 owned prefix 和 reserved image namespace，没有扩大到一般文件删除。

## Fix Round 1

### Review Finding

修复 `TEST-001`：补充真实 public-path、no-network 的 same Shot/role regeneration E2E，并覆盖后续 recovery 对历史 succeeded image attempt 的验证。

### RED Evidence

按 public API 顺序建立场景时依次暴露并保留了以下 RED 证据：

- 首次 image activation 将 Manifest 升级为 2.5 后，`record_dependency_node_applied()` 被旧 schema gate 拒绝：`Dependency results require Manifest 2.3.`。
- 开放 2.5 gate 后，合法 dependency result 更新了 mutable Manifest states，但 standard loader 将 activation-time `candidate_dependency_states_hash` 错当永久相等约束：`active image dependency state hash mismatch`。
- Shot projection 的 fixed-owner apply 未向既有 evidence verifier 提供 prospective graph/state binding，因而无法合法刷新该 stale node。
- 第二次同 role generation 成功后，recovery 对旧 succeeded attempt 错误要求其 asset 仍被当前 Shot 选中：`active generated image provenance is inconsistent`。

### GREEN Implementation

- `_validate_dependency_transition()` 与 `_dependency_result_context()` 正式接受 Manifest 2.5，既有 graph/evidence/revision 校验保持不变。
- Project dependency result 使用 exact prospective applied state 验证 Shot projection evidence，再由原有 writer 原子写入并重新 resolve graph。
- 新增共享 private activation chronology rule：
  - current revision 低于 `base_manifest_revision + 4` 时拒绝；
  - 恰好位于 activation revision 时，必须与 immutable candidate state hash 完全一致；
  - 后续合法 Manifest revision 允许 P5 mutable result 进展，但仍由 standard loader 执行完整 semantic state validation。
- exact replay 复用同一 chronology rule，因此合法 result progress 后仍保持 Provider/preparer/Manifest writes 全为零。
- generic eight-artifact verifier 改为验证 historical attempt 的 immutable candidate Shot selection；当前 active selection 仍由 `verify_active_image_evidence()` 单独严格验证，没有弱化 active tuple、selected asset、graph 或 provenance gate。
- fixture 的 image activation revision 由手工 `+1` 修正为真实四步 lifecycle 的 `+4`；第二张 PNG 使用不同 deterministic RGBA bytes，E2E 得到两个完全不同的十六项 proof paths。

### E2E Acceptance

- 同一 `shot-1/still` 先后使用两个不同 request/output 成功生成。
- 使用 public `record_dependency_node_applied()` 逐个重开并刷新 ready Asset/Shot projection evidence；没有手工伪造最终 Manifest。
- dependency result 后 standard loader 和首次 request exact replay 均成功，replay 外部调用/写入为零。
- recovery revision-idempotent；active Project/Registry/Graph/render/dependency states 不变。
- 两个 succeeded attempts 的 request/result/receipt/PNG/Shot/Project/Registry/Graph 共 16 个不同 immutable proof paths 均由 recovery 重开并报告。
- append-only Registry 同时保留旧、新 generated asset，只有新 asset 被当前 Shot role 选中。
- 总调用计数严格为 Provider `2`、preparer `2`；recovery 与 replay 不增加调用或 Manifest write。

### Additional Regression Coverage

- exact activation revision 的 state hash drift 拒绝。
- Manifest revision rollback 拒绝。
- later legal dependency result 通过 standard loader 与 replay。
- 仅增加 revision 但删除 dependency state 仍由 standard loader 拒绝。
- Manifest 2.5 dependency result/transition gates 保留 P6 QA/review/repair/final-acceptance fields。

### Verification

- Focused E2E/state commit files: `202 passed in 28.78s`。
- Task 10 required five-file suite: `480 passed in 191.06s`。
- Structure and standard loader suite: `157 passed in 13.29s`。
- Architecture Gate: PASS，`0` errors；仅已有 `src/ai_video/production/image.py +27 LOC` warning，本轮未修改该文件。
- Pure `src/ai_video/production/dependency.py` diff from `6001879`: empty。
- `git diff --check`: clean。
- compileall: passed。
- 未使用网络、真实 Provider、merge、push 或 release。
