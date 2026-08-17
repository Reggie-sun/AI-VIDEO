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
