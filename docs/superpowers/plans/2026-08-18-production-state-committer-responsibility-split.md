# ProductionStateCommitter Responsibility Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 production-state 行为或外部契约的前提下，把 `state_commit.py` 拆成职责清晰、无反向依赖的 private domain mixins，并保留 `ProductionStateCommitter` 作为唯一 public writer/recovery façade。

**Architecture:** `state_commit.py` 只保留 compatibility exports、constructor、patch-sensitive loader/lock seams 与 composite class。Review、dependency、render、voice、recovery、generic transaction 和 persistence 分别移动到 `_state_commit_*` private mixins；跨域调用继续使用同一 `self` 的 late-bound methods，因此所有 mutation 共享 project root、file ops、crash injector、exclusive lock 与 final Manifest commit point。

**Tech Stack:** Python 3.11+、stdlib filesystem primitives、Pydantic v2 production models、pytest、现有 deterministic Architecture Harness Gate；无新 dependency、无 network、无 Provider call。

**Spec:** `docs/superpowers/specs/2026-08-17-production-state-committer-responsibility-split.md`

## Global Constraints

- `ProductionStateCommitter` 继续是唯一可实例化 writer/recovery owner；private mixin 不从 package root 导出，也不能被当成独立 writer。
- 不改变 public/direct import names、method signatures、`CommitPhase` values、crash checkpoint order、error code/message、persistence layout、schema、CLI 或 runtime behavior。
- `lock -> validate -> candidate write/fsync -> promote -> reopen verification -> final Manifest replace -> parent fsync` 顺序保持不变。
- `_commit_locked()`、`activate_render_state()`、voice R+1–R+4 和 `_recover_attempts()` 以完整 lifecycle 搬迁，不重写其内部控制流。
- Façade 保留 `fcntl` lock seam，以及对 `load_production_project`、`load_verified_render_state` 的 dynamic lookup；现有 monkeypatch 必须继续命中。
- Private `_state_commit_*` modules 不得 runtime import `state_commit.py`；shared primitives 不得 import domain mixins。
- 新 production modules 不超过 800 effective LOC；correctness-critical transaction cohesion 优先于机械 LOC。
- Architecture baseline 只在完整行为验证通过后显式更新，不得通过 baseline 或 allowlist 隐藏增长。
- Planning snapshot为 clean `062d845 fix: bind p7 lifecycle evidence identities`。每个 task 开始时重新运行 `git status --short`；任何后来出现的 unrelated dirty work均不得 stage、modify、revert或纳入本任务 commits。Implementation base必须是包含 approved spec commit `8fc54ac` 的 current descendant；若 ownership、base ancestry或重叠范围改变，停止并交回 parent。

## File Structure

| File | Responsibility |
| --- | --- |
| `src/ai_video/production/state_commit.py` | sole public façade、compatibility re-exports、constructor、loader wrappers、exclusive lock、mixin composition |
| `src/ai_video/production/_state_commit_contracts.py` | request/path dataclasses、crash protocols、`CommitPhase`、one-use permit types |
| `src/ai_video/production/_state_commit_common.py` | canonical bytes/hash helpers、typed state errors、pure prepare functions |
| `src/ai_video/production/_state_commit_io.py` | `_NativeFileOps` 与 atomic/path/file-descriptor persistence primitives |
| `src/ai_video/production/_state_commit_transaction.py` | generic P2A project/registry commit、validation与 replay verification |
| `src/ai_video/production/_state_commit_review.py` | QA policy、review、approved repair、outcome与 final acceptance lifecycle |
| `src/ai_video/production/_state_commit_dependency.py` | dependency bootstrap、applied/failed lifecycle与 graph verification |
| `src/ai_video/production/_state_commit_render_lifecycle.py` | render attempt/replay/failure/final activation transaction |
| `src/ai_video/production/_state_commit_render_support.py` | render artifact persistence、selection/identity/graph validation |
| `src/ai_video/production/_state_commit_voice_intent.py` | voice attempt、submit intent、terminal outcomes、provider-result validation |
| `src/ai_video/production/_state_commit_voice_candidate.py` | voice activation preparation、graph validation与 candidate verification |
| `src/ai_video/production/_state_commit_voice_activation.py` | voice activation与 end-to-end generation orchestration |
| `src/ai_video/production/_state_commit_recovery.py` | recovery entry、active-state inventory与 recovery decisions |
| `src/ai_video/production/_state_commit_recovery_attempts.py` | exact old/new attempt reasoning与 render/voice reconstruction |
| `src/ai_video/production/_state_commit_recovery_fs.py` | owned-temp cleanup、orphan reporting、nofollow descriptor operations |
| `tests/test_production_state_commit_structure.py` | method ownership、compatibility exports、private import direction与 LOC ratchet |
| `AGENTS.md` | façade + private modules共同构成唯一 committer owner |
| `.architecture/architecture-baseline.json` | verified post-split deterministic debt baseline |

Final façade MRO固定为：

```python
class ProductionStateCommitter(
    _StateCommitReviewMixin,
    _StateCommitVoiceIntentMixin,
    _StateCommitVoiceCandidateMixin,
    _StateCommitVoiceActivationMixin,
    _StateCommitRenderLifecycleMixin,
    _StateCommitRenderSupportMixin,
    _StateCommitDependencyMixin,
    _StateCommitRecoveryMixin,
    _StateCommitRecoveryAttemptsMixin,
    _StateCommitRecoveryFsMixin,
    _StateCommitTransactionMixin,
    _StateCommitIoMixin,
):
```

各 mixin method name不重叠；method间协作只通过 `self` late binding。Façade class body保留 constructor、`project_root`、current render/timeline readers、loader wrappers与 exclusive lock。

---

### Task 1: Extract contracts and pure preparation

**Files:**
- Create: `src/ai_video/production/_state_commit_contracts.py`
- Create: `src/ai_video/production/_state_commit_common.py`
- Create: `tests/test_production_state_commit_structure.py`
- Modify: `src/ai_video/production/state_commit.py`

**Interfaces:**
- Consumes: existing model/path/hash symbols currently imported by `state_commit.py`.
- Produces: unchanged request/path types, `CommitPhase`, crash protocols, durable permits, canonical helpers and `prepare_*` functions, re-exported from `state_commit` with the same object identity.

- [ ] **Step 1: Record the exact base and protect unrelated dirty work**

```bash
git status --short --branch
git rev-parse HEAD
git merge-base --is-ancestor 8fc54ac HEAD
git diff --name-only
python -m scripts.architecture_gate check
```

Expected: `git merge-base --is-ancestor 8fc54ac HEAD` exits `0`；记录当时 exact `HEAD` 为 implementation base；Architecture Gate passes；unrelated dirty paths remain outside every stage set。

- [ ] **Step 2: Write the failing compatibility test**

Create `tests/test_production_state_commit_structure.py`:

```python
from __future__ import annotations

import importlib


def test_contracts_and_prepare_helpers_are_owned_by_private_modules() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    contracts = importlib.import_module("ai_video.production._state_commit_contracts")
    common = importlib.import_module("ai_video.production._state_commit_common")
    contract_names = (
        "PreparedArtifact", "StateCommitRequest", "BeginRenderAttemptRequest",
        "RecordRenderFailureRequest", "ActivateRenderStateRequest",
        "RenderAttemptPaths", "VoiceAttemptPaths", "PreparedVoiceCandidate",
        "CommitPhase", "CrashInjector", "NoopCrashInjector",
        "_DurableReviewAnalysisPermit", "_DurableVoiceSubmitPermit",
    )
    helper_names = (
        "_owned_temp_name", "_canonical_json_bytes", "_canonical_yaml_bytes",
        "_candidate_artifacts_hash", "_dependency_states_hash",
        "prepare_project_registry_commit", "prepare_audio_registry_commit",
        "prepare_dependency_graph_transition",
    )
    for name in contract_names:
        assert getattr(facade, name) is getattr(contracts, name)
    for name in helper_names:
        assert getattr(facade, name) is getattr(common, name)
```

- [ ] **Step 3: Run the test and verify RED**

```bash
python -m pytest -p no:cacheprovider tests/test_production_state_commit_structure.py -q
```

Expected: FAIL with `ModuleNotFoundError` for `_state_commit_contracts`.

- [ ] **Step 4: Move the exact contract/helper blocks**

Move complete definitions without changing bodies:

```text
_state_commit_contracts.py
  PreparedArtifact through NoopCrashInjector
  VoiceCandidatePreparer / VoiceDependencyTransitionPreparer aliases
  _VOICE_PERMIT_TOKEN / _REVIEW_PERMIT_TOKEN
  _DurableReviewAnalysisPermit / _DurableVoiceSubmitPermit
  DurableVoiceSubmitPermit typing alias

_state_commit_common.py
  _GRAPH_ARTIFACT_PHASES / _RESERVED_TARGETS / temp-name limits
  _owned_temp_name through _handle_cleanup_errors
  _validated_transition
  prepare_project_registry_commit
  prepare_audio_registry_commit
  _dependency_states_hash
  prepare_dependency_graph_transition
```

Replace definitions in `state_commit.py` with explicit imports/re-exports:

```python
from ._state_commit_common import (
    _as_state_error, _bundle_hash_from_pointers, _candidate_artifacts_evidence_hash,
    _candidate_artifacts_hash, _canonical_json_bytes, _canonical_yaml_bytes,
    _dependency_states_hash, _handle_cleanup_errors, _is_process_exception,
    _outcome_unknown, _owned_temp_name, _owned_temp_prefix,
    _redact_render_error_message, _stable_voice_terminal_message,
    _state_commit_failed, _state_error, _state_invalid, _state_recovery_failed,
    _state_unsupported, _timestamp, _validated_transition,
    prepare_audio_registry_commit, prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ._state_commit_contracts import (
    ActivateRenderStateRequest, BeginRenderAttemptRequest, CommitPhase,
    CrashInjector, DurableVoiceSubmitPermit, NoopCrashInjector,
    PreparedArtifact, PreparedVoiceCandidate, RecordRenderFailureRequest,
    RenderAttemptPaths, StateCommitRequest, VoiceAttemptPaths,
    VoiceCandidatePreparer, VoiceDependencyTransitionPreparer,
    _DurableReviewAnalysisPermit, _DurableVoiceSubmitPermit,
)
```

Preserve `registry_semantic_sha256` and `canonical_dependency_graph_snapshot_path` as original façade aliases.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py -q
git add src/ai_video/production/_state_commit_contracts.py \
  src/ai_video/production/_state_commit_common.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract state commit contracts"
```

Expected: tests PASS; only Task 1 files are committed.

---

### Task 2: Extract generic transaction and persistence primitives

**Files:**
- Create: `src/ai_video/production/_state_commit_io.py`
- Create: `src/ai_video/production/_state_commit_transaction.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit_structure.py`

**Interfaces:**
- Consumes: Task 1 contracts/common and façade-owned `_exclusive_lock()`.
- Produces: `_StateCommitIoMixin` and `_StateCommitTransactionMixin`; `_NativeFileOps` stays re-exported with one class identity.

- [ ] **Step 1: Add owner assertions and verify RED**

```python
def test_generic_transaction_and_io_methods_have_private_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    io = importlib.import_module("ai_video.production._state_commit_io")
    transaction = importlib.import_module("ai_video.production._state_commit_transaction")
    assert facade._NativeFileOps is io._NativeFileOps
    assert facade.ProductionStateCommitter._commit_locked.__module__ == transaction.__name__
    assert facade.ProductionStateCommitter._write_mutable_atomic.__module__ == io.__name__
    assert facade.ProductionStateCommitter._write_immutable_artifact.__module__ == io.__name__
    assert facade.ProductionStateCommitter._exclusive_lock.__module__ == facade.__name__
```

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py::test_generic_transaction_and_io_methods_have_private_owners -q
```

Expected: FAIL because the modules do not exist.

- [ ] **Step 2: Extract IO/persistence as one mixin**

Move `_FileOps`, `_NativeFileOps` and these complete methods into `_StateCommitIoMixin`:

```text
_write_manifest_atomic, _write_p6_manifest_atomic, _write_mutable_atomic,
_artifact_checkpoint, _write_immutable_artifact, _state_directory,
_validate_artifact_path, _validate_final_path, _validate_cleanup_temp_path,
_validate_relative_components, _ensure_parent_directory, _ensure_directory_chain,
_validate_final_parent, _reject_symlink, _require_same_filesystem
```

The mixin defines no `__init__`; it consumes `self._project_root`, `self._ops`, and `self._crash_injector`.

- [ ] **Step 3: Extract the generic commit lifecycle intact**

Move complete bodies into `_StateCommitTransactionMixin`:

```text
prepare_artifact, commit, _commit_locked, _read_manifest, _validate_request,
_require_pointer_artifact, _validate_replay,
_validate_repair_request_against_manifest, _verify_committed_candidates
```

Keep `_exclusive_lock` in the façade. Replace the render loader call inside `_commit_locked()` with:

```python
state = self._load_verified_render_state(
    self._project_root,
    retained_render_state,
    project=manifest.active_project,
    registry=manifest.active_registry,
)
```

- [ ] **Step 4: Preserve loader/lock seams and compose mixins**

Façade-owned dynamic wrappers:

```python
def _load_production_project(
    self,
    project_path: str | Path,
) -> LoadedProductionProject:
    return load_production_project(project_path)

def _load_verified_render_state(
    self,
    root: Path,
    pointer: RenderStateSnapshotPointer,
    *,
    project: ProjectSnapshotPointer,
    registry: RegistrySnapshotPointer,
) -> RenderStateSnapshot:
    return load_verified_render_state(
        root,
        pointer,
        project=project,
        registry=registry,
    )
```

Compose without copying state:

```python
class ProductionStateCommitter(
    _StateCommitTransactionMixin,
    _StateCommitIoMixin,
):
```

把现有 `__init__`、`project_root`、`_current_render_state`、`_current_resolved_timeline` 与 `_exclusive_lock` 作为该 class 的具体 body保留；包括 `fcntl.flock` 在内的 lock body不变，且不在 `__init__` 缓存 loader。

- [ ] **Step 5: Verify and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
git add src/ai_video/production/_state_commit_io.py \
  src/ai_video/production/_state_commit_transaction.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract state commit transaction core"
```

Expected: PASS including atomicity, `_NativeFileOps`, `state_commit.os.*`, pre/post replace mapping and crash checkpoints.

---

### Task 3: Extract review and dependency lifecycles

**Files:**
- Create: `src/ai_video/production/_state_commit_review.py`
- Create: `src/ai_video/production/_state_commit_dependency.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit_structure.py`

**Interfaces:**
- Consumes: façade loader/current-render/current-timeline seams, lock and shared transaction/io methods.
- Produces: `_StateCommitReviewMixin` and `_StateCommitDependencyMixin` with original methods on the façade.

- [ ] **Step 1: Add owner assertions and verify RED**

```python
def test_review_and_dependency_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    review = importlib.import_module("ai_video.production._state_commit_review")
    dependency = importlib.import_module("ai_video.production._state_commit_dependency")
    committer = facade.ProductionStateCommitter
    assert committer.activate_qa_policy.__module__ == review.__name__
    assert committer.record_final_acceptance.__module__ == review.__name__
    assert committer.bootstrap_dependency_graph.__module__ == dependency.__name__
    assert committer.record_dependency_node_failed.__module__ == dependency.__name__
```

Run the single test; expected failure is missing private modules.

- [ ] **Step 2: Move the complete review boundary**

`_StateCommitReviewMixin` owns unchanged bodies for:

```text
activate_qa_policy, record_review_receipt, begin_review, run_review_analysis,
record_approved_repair_receipt, record_repair_outcome,
record_final_acceptance, _review_request_is_consumed
```

Replace every direct `load_production_project` call in the moved methods with the façade-owned `self._load_production_project` wrapper. Keep `_current_render_state()` and `_current_resolved_timeline()` in the façade for class monkeypatch compatibility.

- [ ] **Step 3: Move the complete dependency boundary**

`_StateCommitDependencyMixin` owns unchanged bodies for:

```text
_dependency_states_hash, bootstrap_dependency_graph,
_bootstrap_dependency_graph_locked, _verify_dependency_candidate,
_validate_request_dependency_transition, _validate_dependency_transition,
_reopen_dependency_graph, record_dependency_node_applied,
record_dependency_node_failed, _dependency_result_context,
_write_dependency_result
```

Keep calls to commit/io/lock helpers late-bound through `self`.

- [ ] **Step 4: Verify and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_review.py tests/test_production_repair.py \
  tests/test_mcp_review.py tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py -q
git add src/ai_video/production/_state_commit_review.py \
  src/ai_video/production/_state_commit_dependency.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract state review and dependency commits"
```

Expected: PASS; review freshness, repair authorization, graph co-activation and replay remain unchanged.

---

### Task 4: Extract render lifecycle without splitting activation invariants

**Files:**
- Create: `src/ai_video/production/_state_commit_render_lifecycle.py`
- Create: `src/ai_video/production/_state_commit_render_support.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit_structure.py`

**Interfaces:**
- Consumes: shared io/transaction and façade `_load_verified_render_state()`.
- Produces: original render methods; `activate_render_state()` remains one method and one final activation point.

- [ ] **Step 1: Add owner assertions and verify RED**

```python
def test_render_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    lifecycle = importlib.import_module("ai_video.production._state_commit_render_lifecycle")
    support = importlib.import_module("ai_video.production._state_commit_render_support")
    committer = facade.ProductionStateCommitter
    assert committer.activate_render_state.__module__ == lifecycle.__name__
    assert committer._write_render_immutable_artifact.__module__ == support.__name__
    assert committer._validate_render_artifacts.__module__ == support.__name__
```

Run the single test; expected failure is missing render modules.

- [ ] **Step 2: Move render lifecycle complete bodies**

`_StateCommitRenderLifecycleMixin` owns:

```text
render_attempt_paths, _ensure_render_attempt_namespace, begin_render_attempt,
_begin_render_attempt_with_status, _replay_render_attempt,
_reconstruct_render_activation_request, record_render_failure,
activate_render_state
```

Do not split or reorder `activate_render_state()`.

- [ ] **Step 3: Move render support complete bodies**

`_StateCommitRenderSupportMixin` owns:

```text
_write_render_manifest_atomic, _write_render_immutable_artifact,
_render_activation_identity, _verify_render_dependency_application,
_same_render_begin, _validate_render_selection, _validate_render_artifacts,
_parse_render_model, _require_render_artifact, _verify_durable_render_graph
```

Replace direct render loader calls with the façade-owned `self._load_verified_render_state` wrapper. Import the shared stdlib `os` module normally so `state_commit.os.open/read/close/unlink` fault injection still affects it.

- [ ] **Step 4: Verify and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py \
  tests/test_production_project.py -q
git add src/ai_video/production/_state_commit_render_lifecycle.py \
  src/ai_video/production/_state_commit_render_support.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract render state lifecycle"
```

Expected: PASS including replay, held-FD verification and atomic Composition/Timeline/Source/Render activation.

---

### Task 5: Extract voice intent, candidate and activation lifecycles

**Files:**
- Create: `src/ai_video/production/_state_commit_voice_intent.py`
- Create: `src/ai_video/production/_state_commit_voice_candidate.py`
- Create: `src/ai_video/production/_state_commit_voice_activation.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit_structure.py`

**Interfaces:**
- Consumes: durable permit contracts and shared io/transaction/dependency methods.
- Produces: original voice API; `_DurableVoiceSubmitPermit` remains nominally identical for `elevenlabs.py`.

- [ ] **Step 1: Add owner/identity assertions and verify RED**

```python
def test_voice_methods_have_domain_owners_and_one_permit_identity() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    contracts = importlib.import_module("ai_video.production._state_commit_contracts")
    intent = importlib.import_module("ai_video.production._state_commit_voice_intent")
    candidate = importlib.import_module("ai_video.production._state_commit_voice_candidate")
    activation = importlib.import_module("ai_video.production._state_commit_voice_activation")
    committer = facade.ProductionStateCommitter
    assert facade._DurableVoiceSubmitPermit is contracts._DurableVoiceSubmitPermit
    assert committer.record_voice_submit_intent.__module__ == intent.__name__
    assert committer._prepare_voice_activation_request.__module__ == candidate.__name__
    assert committer.generate_voice_asset.__module__ == activation.__name__
```

Run the single test; expected failure is missing voice modules.

- [ ] **Step 2: Move voice intent and terminal methods**

`_StateCommitVoiceIntentMixin` owns unchanged bodies for:

```text
voice_attempt_paths, _voice_receipt, _voice_prepared_artifact,
begin_voice_generation, record_voice_submit_intent, _reopen_voice_evidence,
_voice_submit_intent_is_current, _record_voice_terminal,
record_voice_failure, record_voice_outcome_unknown,
_validate_voice_provider_result
```

- [ ] **Step 3: Move candidate preparation and graph validation**

`_StateCommitVoiceCandidateMixin` owns:

```text
_prepare_voice_activation_request
_validate_voice_activation_graph
_verify_voice_committed_candidates
```

- [ ] **Step 4: Move activation/orchestration intact**

`_StateCommitVoiceActivationMixin` owns:

```text
activate_voice_assets
generate_voice_asset
```

Preserve durable request/intent、one-use permit、provider call/result、candidate validation和 final activation顺序。No mixin may define another permit class.

- [ ] **Step 5: Verify and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_state_recovery.py -q
git add src/ai_video/production/_state_commit_voice_intent.py \
  src/ai_video/production/_state_commit_voice_candidate.py \
  src/ai_video/production/_state_commit_voice_activation.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract voice state lifecycle"
```

Expected: PASS; exact replay never resubmits and voice R+1–R+4 semantics remain unchanged.

---

### Task 6: Extract explicit recovery last

**Files:**
- Create: `src/ai_video/production/_state_commit_recovery.py`
- Create: `src/ai_video/production/_state_commit_recovery_attempts.py`
- Create: `src/ai_video/production/_state_commit_recovery_fs.py`
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit_structure.py`

**Interfaces:**
- Consumes: all earlier domain identities, shared io/path primitives and façade loader wrappers.
- Produces: unchanged `ProductionStateCommitter.recover()` and `recover_production_state()` under the same lock.

- [ ] **Step 1: Add owner assertions and verify RED**

```python
def test_recovery_methods_have_domain_owners() -> None:
    facade = importlib.import_module("ai_video.production.state_commit")
    recovery = importlib.import_module("ai_video.production._state_commit_recovery")
    attempts = importlib.import_module("ai_video.production._state_commit_recovery_attempts")
    recovery_fs = importlib.import_module("ai_video.production._state_commit_recovery_fs")
    committer = facade.ProductionStateCommitter
    assert committer.recover.__module__ == recovery.__name__
    assert committer._recover_attempts.__module__ == attempts.__name__
    assert committer._remove_recovery_temp.__module__ == recovery_fs.__name__
    assert committer._require_recovery_file_hash.__module__ == recovery_fs.__name__
```

Run the single test; expected failure is missing recovery modules.

- [ ] **Step 2: Move recovery orchestration/decision methods**

`_StateCommitRecoveryMixin` owns:

```text
recover, _recover_locked, _active_recovery_items, _p6_active_recovery_items,
_recovery_dependency_outcome, _interrupted_dependency_graph_item,
_has_owned_dependency_graph_temp, _dependency_graph_candidate_is_absent,
_candidate_hash_with_optional_graph, _render_graph_recovery_items
```

Replace direct render loader calls with the façade-owned `self._load_verified_render_state` wrapper.

- [ ] **Step 3: Move attempt reconciliation as one block**

`_StateCommitRecoveryAttemptsMixin` owns unchanged bodies for:

```text
_recover_attempts
_render_state_artifacts_hash
_reconstruct_voice_activation_request
```

Do not refactor the old/new identity branches inside `_recover_attempts()`.

- [ ] **Step 4: Move safe filesystem cleanup/orphan inventory**

`_StateCommitRecoveryFsMixin` owns:

```text
_remove_fixed_manifest_temp, _remove_owned_attempt_temps,
_remove_render_attempt_scratch, _remove_recovery_temp,
_preserved_orphan_items, _p6_orphan_items, _dependency_graph_orphan_items,
_render_orphan_items, _attempt_orphan_pair_items, _project_orphan_items,
_registry_orphan_items, _recovery_namespace_entries,
_recovery_directory_descriptor, _recovery_file_descriptor,
_close_recovery_descriptors, _recovery_file_digest, _unlink_recovery_file,
_require_recovery_file_hash, _require_loaded_pointer_identity,
_validate_recovery_project_pointer, _validate_recovery_registry_pointer
```

Use the shared stdlib `os` module object so façade `os.*` monkeypatches still inject faults. Only bounded committer-owned temps may be deleted.

- [ ] **Step 5: Keep the convenience function in the façade**

```python
def recover_production_state(project_root: str | Path) -> RecoveryReport:
    """Explicitly recover P2A state after an interrupted process."""
    try:
        return ProductionStateCommitter(project_root).recover()
    except AiVideoError as exc:
        if exc.code in {
            ErrorCode.PRODUCTION_STATE_BUSY,
            ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
        }:
            raise
        raise _state_recovery_failed(
            "Could not recover production state.",
            exc.technical_detail or str(exc),
        ) from exc
```

- [ ] **Step 6: Verify and commit**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_project.py -q
git add src/ai_video/production/_state_commit_recovery.py \
  src/ai_video/production/_state_commit_recovery_attempts.py \
  src/ai_video/production/_state_commit_recovery_fs.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_commit_structure.py
git diff --cached --check
git commit -m "refactor: extract production state recovery"
```

Expected: PASS including crash-worker exit `91`, `CommitPhase` occurrence, nofollow safety, process-exception preservation, orphan preservation and idempotency.

---

### Task 7: Lock the architecture ratchet, document ownership and verify behavior

**Files:**
- Modify: `tests/test_production_state_commit_structure.py`
- Modify: `AGENTS.md`
- Modify: `.architecture/architecture-baseline.json`

**Interfaces:**
- Consumes: all private mixins and final façade.
- Produces: structural regression protection, durable ownership wording and reviewed post-split baseline.

- [ ] **Step 1: Add final import-direction and LOC tests**

Append:

```python
import ast
from pathlib import Path

PRIVATE_MODULES = (
    "_state_commit_contracts.py", "_state_commit_common.py",
    "_state_commit_io.py", "_state_commit_transaction.py",
    "_state_commit_review.py", "_state_commit_dependency.py",
    "_state_commit_render_lifecycle.py", "_state_commit_render_support.py",
    "_state_commit_voice_intent.py", "_state_commit_voice_candidate.py",
    "_state_commit_voice_activation.py", "_state_commit_recovery.py",
    "_state_commit_recovery_attempts.py", "_state_commit_recovery_fs.py",
)

def _effective_loc(path: Path) -> int:
    return sum(
        1 for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )

def test_private_modules_do_not_import_facade_and_stay_focused() -> None:
    production = Path(__file__).parents[1] / "src/ai_video/production"
    for filename in PRIVATE_MODULES:
        path = production / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports_facade = any(
            isinstance(node, ast.ImportFrom)
            and (
                node.module == "state_commit"
                or any(alias.name == "state_commit" for alias in node.names)
            )
            for node in ast.walk(tree)
        )
        assert not imports_facade
        assert _effective_loc(path) <= 800, filename
    assert _effective_loc(production / "state_commit.py") <= 800
```

If an indivisible method makes a module exceed 800, move adjacent support helpers to the already named support module; never split the transaction method or weaken the assertion.

- [ ] **Step 2: Verify structure/gate before baseline update**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit_structure.py \
  tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q
python -m scripts.architecture_gate check
```

Expected: tests PASS; gate has no growth/cycle ERROR and may report old `state_commit.py` debt as stale/advisory.

- [ ] **Step 3: Make the minimal `AGENTS.md` clarification**

Replace the existing boundary bullet with:

```markdown
- `src/ai_video/production/state_commit.py` 及 private `_state_commit_*` implementation modules：共同实现 P2A 唯一 v2 state writer、snapshot activation、commit-point error mapping 和 explicit recovery；`ProductionStateCommitter` façade仍是唯一 public owner，private modules不得形成第二 writer。
```

- [ ] **Step 4: Explicitly update/review baseline**

```bash
python -m scripts.architecture_gate update-baseline
git diff -- .architecture/architecture-baseline.json
python -m scripts.architecture_gate check
```

Expected: old severe façade debt is removed/reduced to actual post-split metrics; no hidden allowlist; final gate exits `0`.

- [ ] **Step 5: Run closest cross-domain suites**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py tests/test_production_state_recovery.py \
  tests/test_production_hyperframes.py tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py tests/test_production_project.py \
  tests/test_production_dependency.py tests/test_production_selective_rebuild.py \
  tests/test_production_review.py tests/test_production_repair.py \
  tests/test_mcp_review.py tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py \
  tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q
```

- [ ] **Step 6: Run full verification**

```bash
python -m compileall -q src/ai_video src/ai_video_mcp scripts/architecture_gate
python -m pytest -p no:cacheprovider -q
python -m scripts.architecture_gate check
```

Expected: all exit `0`. If unrelated P7 dirty work causes failures, record exact failures and prove the state-commit diff from a clean approved base; do not edit unrelated files.

- [ ] **Step 7: Request independent read-only review**

Review contract:

```text
Verdict: accept / accept with concerns / reject
Check: sole writer, MRO ambiguity, patch-sensitive globals, checkpoint order,
       recovery safety, public imports, module cycles, LOC ratchet,
       accidental behavior edits.
Evidence: exact files/symbols and commands.
Boundary: read-only, no edits, no nested delegation.
```

Parent verifies each blocking claim; any correction reruns its closest suite plus structural tests.

- [ ] **Step 8: Review exact diff and commit final gate/docs files**

```bash
git diff --check
git diff -- src/ai_video/production/state_commit.py \
  'src/ai_video/production/_state_commit_*.py' \
  tests/test_production_state_commit_structure.py AGENTS.md \
  .architecture/architecture-baseline.json
git status --short
git add tests/test_production_state_commit_structure.py AGENTS.md \
  .architecture/architecture-baseline.json
git diff --cached --check
git commit -m "test: ratchet state committer boundaries"
```

Expected: every unrelated file present at implementation start remains unstaged and untouched; split commits contain only plan-owned files.

## Completion Evidence

Final delivery必须报告：created/modified modules及职责；façade physical/effective LOC before/after与最大 private-module LOC；unchanged imports和 transaction/recovery contract；focused/full test counts与 gate output；independent reviewer verdict；task commit hashes；保留的 unrelated dirty files；以及 remaining limits（semantic cohesion、dynamic imports/runtime plugins不由本拆分证明，transaction complexity仍按 correctness boundary保留）。
