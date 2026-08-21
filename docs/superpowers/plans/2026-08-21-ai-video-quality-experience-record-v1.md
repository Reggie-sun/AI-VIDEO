# AI-VIDEO QualityExperienceRecord v1 Implementation Plan

## Status

Executable plan only。当前 slice 只提交本 Plan 与对应 Spec；不得在本 slice 实现代码、修改
Harness policy、创建fixture、rebuild Agent Memory index、运行Provider、生成媒体或开始Pilot。

Implementation 必须以开始当天的 live `main`、current code/tests、exact ownership和 Harness policy
为准。本 Plan 不把 proposed file names、tests或schema描述成 runtime truth。

## Goal

实现一个最小、additive、no-network 的 `Q0 passive capture` data plane：一条 immutable
`QualityExperienceRecordV1` 对应一个 exact Shot generation attempt；一个 immutable
`PilotCaptureCohortV1` + Manifest-delta `PilotAttemptRosterV1`定义prospective completeness；一个
immutable `PilotDatasetIndexV1` 聚合4–8 distinct Shots及roster中的全部attempts；exact field/hash
lookup不依赖Markdown或RAG；sanitized projection只为advisory semantic retrieval提供derived input。

完成runtime slice后，下一次获授权Pilot才可prospective记录Q0 dataset。Implementation acceptance
不等于Pilot GO、Provider authorization、media generation、quality acceptance、Q1/Q2、push或release。

## Contract Checkpoint Before Code

- **Problem boundary:** 新Pilot缺少machine-readable per-attempt comparison/audit record；canonical
  runtime evidence已由Production/P6 owners持有，不得复制lifecycle。
- **Single Production owner:** `ProductionStateCommitter`保持唯一Production writer。
- **Single Q0 owner:** new `ai_video.quality_intelligence.QualityExperienceStore`只写显式的
  non-Production `pilot_dataset_root/quality-experience/v1/`。
- **Old path to replace:** 新Pilot逐Shot只写散落Markdown，随后靠RAG/人工恢复request、parameter、
  artifact、measurement和verdict。历史Markdown保留；runtime implementation不批量改写。
- **Unchanged contracts:** ProductionProject/Manifest/Registry/P5/P6/Planner/Readiness/Router/Provider/
  ResolvedTimeline/HyperFrames/Final Acceptance/Legacy CLI全部不变。
- **Focused first command:** `python -m pytest -p no:cacheprovider tests/test_quality_experience_models.py -q`。

## Exact Future Change Surface

### Create

- `src/ai_video/quality_intelligence/__init__.py`
  - 只导出safe models、pure lookup/projection和`QualityExperienceStore`；不导出raw write primitives。
- `src/ai_video/quality_intelligence/models.py`
  - strict/frozen v1 record、cohort/roster、historical import、pointers、Pilot index、tagged evidence/
    completeness models。
- `src/ai_video/quality_intelligence/store.py`
  - canonical serializer、semantic/file hash、path containment、create-exclusive/no-follow/fsync/reopen、
    exact record/index/import load与zero-write replay。
- `src/ai_video/quality_intelligence/dataset.py`
  - pure 4–8 Shot aggregation、index projection verification、exact typed filtering；no IO owner duplication。
- `src/ai_video/quality_intelligence/rag_projection.py`
  - pure deterministic sanitized Markdown renderer；不写docs、不build/search index。
- `tests/test_quality_experience_models.py`
- `tests/test_quality_experience_store.py`
- `tests/test_quality_experience_dataset.py`
- `tests/test_quality_experience_rag_projection.py`
- `tests/fixtures/quality_experience/v1/prospective_success.json`
- `tests/fixtures/quality_experience/v1/prospective_failure.json`
- `tests/fixtures/quality_experience/v1/outcome_unknown.json`
- `tests/fixtures/quality_experience/v1/pilot_cohort.json`
- `tests/fixtures/quality_experience/v1/pilot_attempt_roster.json`
- `tests/fixtures/quality_experience/v1/legacy_incomplete.json`

### Modify only after RED evidence requires it

- `.agent/harness/policy.yaml`
  - add `quality_intelligence_tests` and map only new package/tests; include task Architecture Gate。
- `tests/test_agent_harness.py`
  - exact route, overlap, unknown-path fallback与command coverage。
- `docs/agent-primary-contract-matrix.md`
  - add advisory Q0 surface、single store owner、forbidden Production/RAG alternate paths、focused tests。
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
  - only after implementation acceptance，记录实际implemented behavior与Q1/Q2 deferred boundary。

### Read/reuse, do not modify by default

- `src/ai_video/production/{models.py,project.py,registry.py,hashing.py,paths.py}`；
- `src/ai_video/production/{video.py,video_artifact.py,local_video.py,shot_router.py}`；
- `src/ai_video/quality_gates/_readiness_models.py`；
- `src/ai_video/production/{_state_commit_review.py,_state_commit_repair.py}`；
- `src/ai_video/agent_memory/**`、`scripts/agent_memory.py`。

Implementation 不把new schema塞进`production/models.py`，不新增Manifest fields或state-commit mixin，
不修改Agent Memory corpus/index contract。若真实dependency evidence要求越过上述surface，先修订Spec/
Plan并重新review，不能让writer自行扩大。

## Implementation Sequence

### T0 — Revalidate base, ownership, and old path

1. 检查 `git status --short --branch`、`git rev-parse HEAD`、
   `git rev-list --left-right --count origin/main...HEAD`、live agents和external writers的exact
   `allowed_paths`；same-file overlap时停止并让用户决定。
2. 记录 implementation base commit；确认Spec/Plan已在base、unrelated dirty files不进入scope。
3. 用`rg`重证canonical fields、P6 pointers、current Agent Memory corpus和不存在Q0 source owner。
4. 运行现有focused baseline（read-only/no-network）：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_agent_memory.py -q
```

Pre-existing failure先隔离；不得扩大Q0修复面。

### T1 — RED/GREEN strict models and exact attempt identity

1. 先写RED tests：prospective success/failure/outcome-unknown、strict/no-extra/frozen、canonical
   ordering、NFC、duplicate parameter/rubric rejection、attempt uniqueness、backward-only predecessor、
   bounded free text/redaction、raw prompt/secret/signed URL/absolute path denylist、deterministic
   `AttemptIdentityKey`和Manifest-derived `attempt_sequence`。
2. Run RED：

```bash
python -m pytest -p no:cacheprovider tests/test_quality_experience_models.py -q
```

RED必须是missing symbols/behavior，不接受collection/import/fixture error冒充。
3. 实现minimum models；prospective required identity不得unknown，provider-specific不适用使用tagged
   `not_applicable`。
4. Run GREEN同一command。

### T2 — RED/GREEN serializer, immutable store, and exact reopen

1. RED覆盖semantic `content_hash`、final `file_sha256`、canonical paths、create-exclusive、no-follow、
   fsync/reopen、same-bytes zero-write、different-bytes collision、tamper/symlink/traversal/partial拒绝；
   cross-process exclusive store lock必须覆盖strict scan -> conflict check -> promotion -> reopen；跨两次
   store call和并发writers的same attempt + different bytes必须typed conflict，same attempt + same bytes
   必须zero-write。
2. 证明store只写explicit dataset root；传入Production `state/assets/creative/runs`或Agent Memory index
   root必须fail closed。Monkeypatch Provider、analyzer、recovery、committer入口，call counts保持0。
3. Run RED/GREEN：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py -q
```

4. Store不得scan latest、生成mutable pointer、删除orphan或自动recover。

### T3 — RED/GREEN historical imports

1. Fixture保留明确known、unknown、incomplete、not_applicable fields与source spans。
2. RED证明缺证据字段不能known；RAG score、文件名、later defaults不能作为evidence；import不能转换成
   prospective record。
3. RED/GREEN：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py \
  -k 'historical or legacy or incomplete or unknown' -q
```

不得批量扫描/改写`docs/record_for_agent/`；fixture只建模migration contract。

### T4 — RED/GREEN Pilot dataset aggregation and exact lookup

1. 先从strict-read base Manifest构造immutable cohort + `ManifestObservationV1`，再提供terminal Manifest。
   RED证明base observation保存revision/file hash/attempt count + ordered-ID hash但不复制active lifecycle；
   roster只包含
   terminal-minus-base的exact `video_generation` attempts，reopen request绑定cohort Shot，sequence来自
   terminal Manifest order；domain-separated prefix encoding、`base_count <= terminal_count`、wrong project、
   non-forward revision、base IDs非exact prefix、wrong operation/Shot/generation、duplicate、missing request
   与tamper均有tests。
2. RED fixtures构造4 distinct Shots baseline，再覆盖8 Shots upper bound、multiple attempts per Shot、
   failure->repair lineage、duplicate attempt、missing failed attempt、extra attempt、3/9 Shots、foreign
   pilot/project、tampered pointer、historical import、projection mismatch和noncanonical order。
3. Index record-key set必须与roster exact相等；entry只能来自reopened record，禁止caller自报Provider/
   verdict/Shot projection。
4. RED/GREEN：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_dataset.py \
  tests/test_quality_experience_store.py -q
```

5. Exact lookup tests必须在 `.agent/memory/index/` absent、stale或unreadable时通过；覆盖
   `list_dataset_pointers(pilot_id)`、hash lookup和
   project/Scene/Shot/attempt/generation/Provider/profile/capability/model/outcome/verdict filters，missing/
   ambiguous fail closed。

### T5 — RED/GREEN derived RAG projection without RAG ownership

1. RED snapshot/structured assertions：projection含`authority=advisory_experience`、dataset/record hashes、
   evidence boundaries；不含raw prompt、negative prompt、Provider response、signed URL、absolute path、
   secret、private reviewer identity或unbounded analyzer payload。
2. 证明projection renderer只返回bytes；filesystem write、Agent Memory build/search、Production mutation
   call counts均0。
3. RED/GREEN：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_rag_projection.py \
  tests/test_agent_memory.py -q
```

不修改Agent Memory source/index。未来把curated summary写入`docs/record_for_agent/`与explicit rebuild是
独立docs/control-plane task，不是Q0 capture side effect。

### T6 — Harness route and architecture boundary

1. 先在`tests/test_agent_harness.py`写RED route tests：new source/test paths选择
   `quality_intelligence_tests + task_architecture_gate`；docs-only仍只有always `scope_diff_check`；
   unknown paths保持fallback。
2. 修改policy和对应description；不得把Q0 route映射到live Provider/media/Agent Memory rebuild。
3. Run：

```bash
python -m pytest -p no:cacheprovider tests/test_agent_harness.py -q
python -m scripts.architecture_gate check
```

4. 运行exact route inspection：

```bash
python scripts/agent_harness.py inspect \
  --path src/ai_video/quality_intelligence/models.py
python scripts/agent_harness.py inspect \
  --path tests/test_quality_experience_models.py
python scripts/agent_harness.py inspect \
  --path docs/superpowers/specs/2026-08-21-ai-video-quality-experience-record-v1.md
python scripts/agent_harness.py inspect \
  --path docs/superpowers/plans/2026-08-21-ai-video-quality-experience-record-v1.md
```

### T7 — Integrated no-side-effect acceptance and canonical docs

1. Run focused suite：

```bash
python -m pytest -p no:cacheprovider \
  tests/test_quality_experience_models.py \
  tests/test_quality_experience_store.py \
  tests/test_quality_experience_dataset.py \
  tests/test_quality_experience_rag_projection.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_agent_memory.py \
  tests/test_agent_harness.py -q
```

2. 用call counters和tree snapshot证明Provider/analyzer/committer/recovery/activation/RAG build均0，
   Production root bytes/mtimes未变化。
3. 只在tests通过后更新matrix/baseline/roadmap；不得写Pilot或quality acceptance为completed。
4. 独立native reviewer检查second truth、secret/privacy、historical inference、index projection mismatch、
   exact lookup/RAG separation和test realism。Parent逐项验证review claims。

## Required Fixtures And Acceptance Matrix

| Case | Must prove | Must not happen |
| --- | --- | --- |
| prospective success | exact planning/router/provider/input/output/reopen/human bindings | fetch/activation/GO互相冒充 |
| known failure | exact attempt and typed failure with no fabricated artifact | missing output silentlydefault success |
| outcome unknown | separate terminal boundary and no retry claim | collapse to failure/success |
| repair/new attempt | newattempt/newrecord + backward predecessor | overwrite failed record或P6 authorization |
| attempt collision | cross-call/concurrent lock + scan enforces one key/record | two hashes for one attempt |
| legacy incomplete | known fields carry source span；others typed unknown/incomplete | infer seed/profile/hash/verdict |
| 4 and 8 Shots | accepted cardinality, multiple attempts allowed | countrecords代替distinct Shots |
| 3 or 9 Shots | validator rejects | silentlytruncate/expand |
| cohort/roster closure | terminal-minus-base Manifest attempts all represented once | omit failed/extra/wrong-Shot attempt |
| index mismatch | reopen catches copied-field drift | index成为第二truth |
| exact lookup | works without Agent Memory | semantic fallback for exact miss |
| RAG projection | hashes/authority/redaction preserved | raw prompt/secret/URL/private PII/index build |
| no-side-effect | onlydataset root changes | Production/Provider/analyzer/recovery mutation |

## Schema And Compatibility

- No Production/Manifest/Registry/P6 schema migration。
- New Q0 record/cohort/roster/index/import schemas start at`1.0` and are additive outsideProduction root。
- Reader只接受exact supported schema；future version需新migration/spec，不原地改v1 bytes。
- Historical Markdown remains byte-identical；imports是new evidence artifacts，不是backfill。
- No dependency、database、service、public CLI、background job或network。

## Rollback

Runtime code rollback只revertnew `quality_intelligence` package、tests、Harness route与verified canonical docs；
不得downgrade或修改Production state。已完成records/indexes保持immutable JSON，可由matching version reader
审计；rollback不删除dataset root。若pre-acceptance implementation失败，保留test fixtures，revert仅限
task-owned code/docs/policy files，且不得reset unrelated work。

## Harness, Commit, And Publication Boundary

Implementation完成时：

1. review exact diff和target ownership；`git diff --check`；
2. 只stage task-owned files；对exact non-empty staged snapshot运行`make harness-verify`；
3. 用`make harness-receipt RECEIPT=<fresh-path>`验证scope、policy、artifact hashes和freshness；
4. 只commit task-owned files，报告implementation base、HEAD、receipt和local-vs-origin truth；
5. 不push/release，除非当前task另有明确授权。

只有fresh passing implementation receipt出现后，下一次已授权Pilot才可写prospective Q0 records。
即使implementation完成，也不得声称Pilot、RAG rebuild、Q1/Q2、automatic learning/selection、P6 quality
acceptance或Final Acceptance完成。

## Current Docs-Only Slice Verification

本slice只允许修改本Plan和对应Spec。Required sequence：

```bash
git add \
  docs/superpowers/specs/2026-08-21-ai-video-quality-experience-record-v1.md \
  docs/superpowers/plans/2026-08-21-ai-video-quality-experience-record-v1.md
git diff --cached --check
python scripts/agent_harness.py inspect --staged
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
git commit -m "docs: define quality experience record v1"
```

Harness current policy将两条路径映射到`documentation`，加always `scope_diff_check`；本slice不得修改
policy以制造更宽或更窄的docs gate。Receipt只证明exact staged docs patch通过current policy，不证明
runtime implementation或Pilot readiness。
