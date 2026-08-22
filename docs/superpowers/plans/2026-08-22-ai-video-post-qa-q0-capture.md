# AI-VIDEO Post-QA Q0 Capture Implementation Plan

## Status

Completed locally。本 Plan 已在base `d9dcdbe572050fbacb28ca5147c84b996445f8bf`的authorized
worktree内实现。最终 executable evidence为focused `319 passed`、Manifest compatibility
`504 passed, 3 skipped`、full suite `2900 passed, 4 skipped`、Architecture Gate `PASS (0 errors)`与
native reviewer `accept with concerns`；exact staged snapshot仍必须由本任务最终fresh Harness receipt证明。
本 Plan 的状态本身不替代receipt，也不表示push/release或automatic product caller存在。

## Governing Artifacts

- Spec（本 slice）：`docs/superpowers/specs/2026-08-22-ai-video-post-qa-q0-capture.md`。
- Q0 data plane：`docs/superpowers/specs/2026-08-21-ai-video-quality-experience-record-v1.md`、
  `docs/superpowers/plans/2026-08-21-ai-video-quality-experience-record-v1.md`。
- Continuity lifecycle：`docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`、
  `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`。
- Planning/implementation base：commit `d9dcdbe572050fbacb28ca5147c84b996445f8bf`（本轮已由
  `git rev-parse HEAD`复核）。

`AGENTS.md`、`docs/agent-primary-contract-matrix.md` 与 Harness policy 优先于本 Plan。若实施中发现
冲突或需要超出 Spec 的 scope，停止并报告，不得由实施者自行扩大。

## Goal

在不新增第二 writer、第二 QA truth、automatic caller、CLI、dependency 或 network path 的前提下：

1. 增加 additive Manifest `2.10` continuity capture checkpoint，使 continuity PASS 与 FAIL 都在
   adjudication 之前拥有 durable、可 strict reopen 的 exact fetch artifact、`VideoProbeReceipt`、
   `VideoProvenanceReceipt` 与 evaluator intent/evidence；
2. 让 `adjudicate_generated_shot_continuity()` 之后的判定保持 pure，非 PASS 仍 fail closed 且不 activation；
3. 在 `ai_video.quality_intelligence` 增加显式 post-QA capture API，把该 attempt 落成一条 immutable
   `QualityExperienceRecordV1`，只写显式 non-Production `pilot_dataset_root/quality-experience/v1/`。

Implementation acceptance 不等于 Pilot GO、dataset 完成度、Provider authorization、媒体生成、
quality/Final Acceptance、push 或 release。

## Contract Checkpoint Before Code

- **Single Production owner:** `ProductionStateCommitter`（不变）。
- **Single Q0 owner:** `ai_video.quality_intelligence` / `QualityExperienceStore`（不变）。
- **Dependency direction:** Production 不得 import Q0；capture caller 显式驱动。
- **Old path to replace:** 手工拼装 record 字段；continuity FAIL 只留 typed error 而无 durable
  artifact/probe/provenance evidence。
- **Authorized additive contract:** record schema `1.1`新增独立 continuity evidence binding；历史 `1.0`
  保持兼容，P6 observations 不得承载 continuity pointer；runtime lineage 只能由 strict reopen 派生，未持久化
  项使用 schema `1.1` tagged `not_applicable`，不得由 caller 补造。
- **Unchanged contracts:** Registry schema、artifact layout public contract、P6 lifecycle、Router/Planner/
  ReadinessGate、Legacy CLI/Manifest/layout、default no-network。
- **Focused first command:**
  `python -m pytest -p no:cacheprovider tests/test_production_continuity_evaluator.py -q`。

## Exact Change Surface

### Create

- `src/ai_video/quality_intelligence/capture.py`
  - 纯 orchestration + strict reopen + 映射到既有 record models；只通过 `QualityExperienceStore` 写入。
- `src/ai_video/quality_intelligence/_capture_contracts.py`
  - public request 与 exact analyzer/human review document pointer contracts。
- `src/ai_video/quality_intelligence/_capture_human.py`
  - human fallback/rubric/document exact cross-check 与 `GO/NO_GO/NOT_REVIEWED` projection。
- `src/ai_video/quality_intelligence/_capture_p6.py`
  - 只 strict reopen 实际存在的 Review/Repair/Final Acceptance pointers。
- `tests/test_quality_experience_capture.py`

### Modify only after RED evidence requires it

- `src/ai_video/production/models.py`、`_lifecycle_schema.py`、`paths.py`：additive `2.10` capture
  checkpoint state 与 canonical pointer paths。
- `src/ai_video/production/_state_commit_video_continuity.py`、`_state_commit_video_candidate.py`、
  `_state_commit_video.py`：checkpoint 顺序、bytes 复用 seam 与 recovery。
- `src/ai_video/production/_video_project_reader.py`：strict reopen 新 pointer。
- `src/ai_video/quality_intelligence/__init__.py`：只导出新的 capture entry point。
- `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`：按真实 changed paths 路由。
- `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、
  `docs/v0.2-agentic-production-roadmap.md`：只在实现通过验证后记录 actually implemented behavior。

### Read/reuse, do not modify by default

- `src/ai_video/production/{review.py,continuity_evaluator.py,video_artifact.py,registry.py,project.py}`；
- `src/ai_video/quality_intelligence/{models.py,store.py,dataset.py,rag_projection.py}`；
- `src/ai_video/agent_memory/**`。

若真实 dependency evidence 要求越过上述 surface（例如必须改 Registry schema、必须新增 public layout
directory、必须让 Production import Q0），立即停止并请求独立授权，不得静默扩大。

## Implementation Sequence

每个 task 使用严格 RED/GREEN：先写 failing tests 并确认 RED 是 missing symbol/behavior（不接受
collection error、import error 或 fixture error 冒充 RED），再实现最小 GREEN，然后重跑同一 focused
command。

### T0 — Revalidate base, ownership, and old path

1. `git status --short --branch`、`git rev-parse HEAD`、
   `git rev-list --left-right --count origin/main...HEAD`；确认无 overlapping writer 与 unrelated dirty
   files 进入 scope；目标文件冲突时停止并报告。
2. 记录 implementation base commit，并与 planning base `d9dcdbe` 的差异一起报告。
3. 用 `rg` 复核当前 continuity checkpoint 顺序、Manifest schema literals、`VideoProbeReceipt`/
   `VideoProvenanceReceipt` 生成点与 Q0 record 必填字段。
4. 运行 read-only baseline（no-network）：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py -q
```

Pre-existing failure 先隔离并报告；不得扩大本 slice 修复面。

### T1 — RED/GREEN Manifest 2.10 capture checkpoint schema

1. RED：additive capture checkpoint state/pointer 的 strict/frozen 校验；pointer 必须绑定 evaluation
   fingerprint、artifact SHA-256、receipt content hash 与 canonical content-addressed path；`2.9`
   attempt 携带新 pointer 必须拒绝；`2.10` attempt 缺 pointer 必须拒绝；历史 `2.0`–`2.9` reopen 保持通过。
2. RED 命令：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_continuity_evaluator.py -q
```

3. GREEN：实现最小 additive schema 与 canonical paths，不改 Registry schema、不改既有 receipt payload/hash。
4. 重跑同一命令。

### T2 — RED/GREEN committer capture checkpoint ordering

1. RED：固定顺序 `intent -> evidence -> capture checkpoint -> adjudication`；checkpoint 写入 exact fetch
   artifact、`VideoProbeReceipt`、`VideoProvenanceReceipt`；checkpoint 不重新 fetch/probe/extract/运行
   evaluator（monkeypatch call counters 保持 0）；单一 writer，no-follow、fsync、reopen 验证；
   tampered/wrong-artifact/wrong-request/wrong-policy/stale pointer fail closed。
2. RED/GREEN 命令：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_state_commit.py -q
```

3. 不得引入第二 writer、mutable pointer、自动 recovery 或 orphan 删除。

### T3 — RED/GREEN PASS/FAIL symmetry and pure adjudication

1. RED：continuity PASS 路径 checkpoint 之后照常 candidate/activation；continuity FAIL 路径在 checkpoint
   之后仍抛出既有 typed error、不 activation、不进入 Registry/P3/P4，但 durable evidence 与 PASS 对称；
   adjudication 本身无 durable write、无 evaluator/sampler/human fallback 再执行。
2. RED：checkpoint 前后各 crash point 的 exact retry/recovery 不重复 side effect、不产生第二份
   artifact/receipt identity、不删除完整 orphan evidence；exact replay counters 为 0。
3. RED/GREEN 命令：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_state_recovery.py \
  tests/test_production_local_video_state.py -q
```

### T4 — RED/GREEN post-QA capture API

1. RED：capture 只接受 exact pointers 与 strict-reopened typed objects；逐项 rehash 验证 Manifest
   revision/file hash、attempt/generation identity、capture pointer、probe/provenance receipt、evaluator
   evidence 与 artifact bytes；mismatch/stale/tamper/wrong-attempt/symlink escape/containment 违规 typed
   fail closed。
2. RED：PASS 映射为 `succeeded/activated` 或 `succeeded/candidate`；FAIL 映射为 `succeeded/fetched` +
   `not_candidate`，且 outcome boundary 明确否认 candidate/activation/quality acceptance；schema `1.1`
   独立保存 continuity checkpoint，schema `1.0` 保持兼容。
3. RED：analyzer evidence 必须完整（canonical Q0 measurement set、排序唯一、`subject_id` 等于 artifact
   `asset_id`），并通过 content-addressed `analysis/**` source-document pointer 做 no-follow strict reopen；
   缺失、篡改、file/artifact SHA 或反序列化 item 不一致均 fail closed，capture 不自行运行 analyzer、
   不用 evaluator measurement 冒充 `video-analysis` measurement。
4. RED：human review 只允许 `GO`/`NO_GO`/`NOT_REVIEWED`，reviewer 保持 pseudonymous，rubric 绑定 exact
   ID/version/hash；human `GO` 不得映射为 `QaVerdict.PASS`、candidate、activation 或 Final Acceptance；
   human fallback 结论不得写成 model observation。
5. RED：Q0-only metadata 必须由 caller 显式提供且 bounded/NFC/redacted；不得从 runtime、文件名、时间
   邻近、默认 profile 或 RAG 结果推断。
6. RED：P6 pointer 只保存 exact kind/path/content hash/file hash 与观察到的 freshness；无 receipt 时
   `not_present` 且无 pointer；不得反推 receipt 或 Manifest state。
7. RED/GREEN 命令：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_capture.py \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py -q
```

### T5 — RED/GREEN boundary, privacy, replay, and no automatic caller

1. RED：capture 只写显式 dataset root；传入 Production `state/`、`assets/`、`creative/`、Legacy `runs/`
   或 Agent Memory index root 必须 fail closed。
2. RED：same `AttemptIdentityKey` + same canonical bytes 为 zero-write；same key + different bytes 为
   typed conflict；capture 失败不留 partial record。
3. RED：privacy denylist（raw prompt/response、signed URL、header/cookie、credential、absolute home
   path、reviewer PII、大块 analyzer payload）在 record、error、`repr`、fixture 与 projection 中全部被拒。
4. RED：Provider/renderer/analyzer/committer/recovery/activation/Agent Memory build/search call counts 为
   0，Production root bytes 与 mtime 不变。
5. RED：`src/ai_video/production/**` 与其他 Production runtime module 不 import
   `ai_video.quality_intelligence`；不存在 automatic capture caller。
6. RED/GREEN 命令：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_capture.py \
  tests/test_quality_experience_dataset.py \
  tests/test_quality_experience_rag_projection.py \
  tests/test_agent_memory.py -q
```

### T6 — Harness route and architecture boundary

1. RED：在 `tests/test_agent_harness.py` 固定新 source/test paths 的 exact route 与 fallback 行为；
   docs-only change 仍只命中 documentation route 与 always `scope_diff_check`。
2. 仅在 RED 证明必要时修改 `.agent/harness/policy.yaml`；不得把本 slice 路由到 live Provider、媒体生成
   或 Agent Memory rebuild。
3. 命令：

```bash
python -m pytest -p no:cacheprovider tests/test_agent_harness.py -q
python -m scripts.architecture_gate check
python scripts/agent_harness.py inspect --path src/ai_video/quality_intelligence/capture.py
python scripts/agent_harness.py inspect --path src/ai_video/production/_state_commit_video_continuity.py
python scripts/agent_harness.py inspect --path tests/test_quality_experience_capture.py
```

### T7 — Integrated verification, docs closure, review, and commit

1. Focused integrated suite：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_registry.py \
  tests/test_production_review.py \
  tests/test_production_continuity_evaluator.py \
  tests/test_production_video.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_local_video_state.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py \
  tests/test_quality_experience_dataset.py \
  tests/test_quality_experience_rag_projection.py \
  tests/test_quality_experience_capture.py \
  tests/test_agent_memory.py \
  tests/test_agent_harness.py -q
```

2. Architecture 与 full verification（changed paths 跨 shared Production owner 时必须执行）：

```bash
python -m scripts.architecture_gate check
python -m pytest -p no:cacheprovider -q
```

3. 只在上述验证通过后，同步 `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`
   与 `docs/v0.2-agentic-production-roadmap.md`，只记录 actually implemented behavior 与仍未验证边界；
   不得把 Pilot、dataset 完成度或 quality acceptance 写成已完成。
4. 独立 native review：逐项检查第二 truth、PASS/FAIL 对称性、pure adjudication、schema 兼容、privacy/
   redaction、P6 反推、依赖方向、automatic caller 与 test realism（是否真的走 production seam 而非
   裸解析）。Parent 逐项验证 review claims。
5. Harness、staged receipt 与 task-only commit：

```bash
git diff --check
git add <exact-task-owned-files>
git diff --cached --check
python scripts/agent_harness.py inspect --staged
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
git commit -m "feat: add post-QA Q0 capture"
```

只 stage task-owned files；不得 `git add -A`、不得 reset/checkout/clean unrelated work、不 push、不
release，除非另有明确授权。

## Acceptance Matrix

| Case | Must prove | Must not happen |
| --- | --- | --- |
| continuity PASS | checkpoint + candidate/activation + capture record 为 `succeeded/activated` 或 `succeeded/candidate` | fetch 冒充 activation 或 quality acceptance |
| continuity FAIL | 与 PASS 对称的 durable artifact/probe/provenance/evaluator evidence + `succeeded/fetched` + `not_candidate` | FAIL 被 activation、或 durable evidence 缺失 |
| pure adjudication | verdict 只从 durable evidence 派生 | adjudication 触发 write 或再次运行 evaluator/human fallback |
| historical manifests | `2.0`–`2.9` reopen/recovery 不变 | `2.9` 偷带 `2.10` pointer 或历史 hash 漂移 |
| retry/recovery | 复用既有 checkpoint、zero extra side effect | 重复 fetch/probe/evaluator 或第二份 receipt identity |
| analyzer completeness | canonical Q0 measurement set 完整且绑定 subject | partial analyzer 静默通过或 capture 自跑 analyzer |
| human fallback | `GO/NO_GO/NOT_REVIEWED` 与 pseudonymous rubric binding | human 结论伪装 model observation 或映射为 PASS |
| P6 pointers | exact hashes + observed freshness，无时 `not_present`；累积repair outcomes为`stale` | 历史outcome冒充fresh，或从 Q0 反推 receipt/Manifest state |
| privacy | denylist 在 record/error/repr/fixture/projection 全部生效 | raw prompt/secret/URL/PII 泄漏 |
| replay/conflict | same bytes zero-write、different bytes typed conflict | 覆盖已 sealed record |
| dependency direction | Production 不 import Q0，无 automatic caller | committer/adapter/CLI 自动触发 capture |

## Schema, Compatibility, And Rollback

- Manifest `2.9 -> 2.10` 为 additive；只有携带新 capture pointer 的 attempt 要求 `2.10`。
- `QualityExperienceRecordV1` schema `1.1` additive 增加独立 continuity evidence binding；schema `1.0`
  canonical bytes/validation 保持兼容；schema `1.1`允许 runtime 未持久化 lineage 使用 tagged
  `not_applicable`，但 public capture request 不接受 caller runtime projection。Registry schema、artifact layout public contract、Legacy CLI/
  Manifest/layout 不变。
- 无新 dependency、CLI、service、queue、database、background job 或 network path。
- Rollback：revert 新的 capture module/tests、Manifest `2.10` additive schema、committer checkpoint seam
  与已验证的 canonical docs；不得 downgrade 或修改既有 Production state，不得删除已写入的 immutable
  evidence 或 dataset records，不得 reset unrelated work。

## Reporting Boundary

Final delivery 必须报告：changed files、每条实际执行过的 verification command 及其结果、Harness receipt
的 repository-relative path、implementation base 与 HEAD、local-vs-origin publication state、remaining
risk 与未验证区域。未实际执行的 live/provider/media/quality 验证必须显式标注为未验证，不得由历史证据
或本 Plan 推断。本 Plan 的存在不证明任何 task 已完成。
