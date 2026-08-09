# AI-VIDEO Agentic Production Harness P2A Production State Commit Protocol Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在 accepted P2 Production Project Core 之上实现唯一的 v2 production state writer，使 immutable project/registry snapshots、attempt state 和 `ProductionManifest` active pointers 以可恢复、可 crash-inject 验证的顺序持久化。

**Architecture:** `ProductionManifest` 继续是唯一 mutable lifecycle/active-revision truth；新的 `src/ai_video/production/state_commit.py` 独占 staging、file/directory fsync、immutable promotion、Manifest atomic replace、attempt failure persistence 和 restart recovery。`project.py` 与 `registry.py` 保持 read-only verifier，Legacy `manifest.py`、`pipeline.py`、Manifest v1 和 `runs/**` 不参与 v2 transaction。

**Tech Stack:** Python 3.11+、Pydantic v2、PyYAML、stdlib `os`/`fcntl`/`hashlib`/`json`/`tempfile`、现有 `AiVideoError`/`ErrorCode`、pytest、subprocess crash-injection fixtures；不新增 runtime dependency，不联网。

---

Status: Docs-only implementation planning. This document is not P2A runtime implementation authorization.

## Problem Boundary

P2A 只建立以下 transaction：

```text
accepted P2 immutable project + registry models
+ explicit expected Manifest revision
+ exact project-root-contained artifact payloads and hashes
        |
        v
atomically persist attempt=running (active pointers unchanged)
        |
        v
write owned temporary files beside final destinations
-> flush + fsync each file
-> promote without overwriting immutable content
-> fsync each parent directory
-> reopen and verify exact bytes/domain hashes
        |
        v
write next ProductionManifest temp
-> flush + fsync file
-> atomic replace state/manifest.json   <-- commit point
-> fsync state directory
        |
        v
recover/clean owned partial temporaries;
report complete unreferenced snapshots as orphans
```

P2A 不创建 Story、Shot、Asset file、timeline、renderer source、render、Audio/Caption、Dependency Graph、Provider request 或 QA receipt。它只提供 future slices 可复用的 durable commit boundary；future domain 仍必须在自己的 slice 中定义 schema、validation 和 pointer semantics。

## Execution Authorization Gate

本 plan 可以现在审查和接受，但实施前必须再次获得明确授权。实施授权必须同时接受以下 P2A-owned schema/layout change：

- 现有 flat v2 `ProductionManifest` fields 被一个 manifest-owned project pointer 和一个 manifest-owned registry pointer 取代；不保留两组 active-pointer owner；
- versioned project snapshots 使用 `state/projects/project.<revision>.<content_hash>.yaml`；
- registry snapshots 继续使用 `assets/registry.<revision_id>.json`；
- `state/manifest.json` 是唯一 transaction commit point；
- `state/commit.lock` 是 POSIX local writer serialization file；
- P2 root `project.yaml` 保持合法 immutable entry snapshot/entrypoint，但在新 revision 激活后不再被误当作 active truth；loader 从 Manifest-selected snapshot 读取 active project；
- implementation target 只承诺当前 POSIX/local filesystem；非 POSIX 平台 typed-fail，不宣称跨平台 power-loss equivalence。

如果用户不接受这些变化，停止实施并先修订本 plan；不得在代码中临时保留 flat pointer 与 nested pointer 两套控制面。

## Current Repository Truth

2026-08-09 的只读核对结论：

| Surface | Current Fact | P2A Decision |
| --- | --- | --- |
| Git | local `main` HEAD `f600ca2`; accepted P2 commit `a5be154`; worktree clean before this plan; `origin/main` behind local main | plan 可写；runtime implementation 仍需新授权和 feature branch |
| v2 state schema | `production/models.py::ProductionManifest` 只有 project revision/hash 和 registry revision | P2A 在同一 schema owner 中完成 pointer/attempt contract |
| v2 reader | `project.py::load_production_project()` 先读 Manifest，再读 root `project.yaml`，并按 inferred registry filename 加载 registry | 改为只读 Manifest-selected exact project/registry paths；不加入写逻辑 |
| registry verifier | `registry.py::registry_semantic_sha256()` 和 `load_asset_registry()` 已验证 semantic hash、filename、asset bytes 和 containment | writer 复用 verifier；不复制第二种 registry hash |
| Legacy writer | `manifest.py::atomic_write_manifest()` 写 `RunManifest`，只有 temp + replace，没有 P2A file/directory fsync contract | 保持 Legacy owner，不抽取、不扩展为 v2 writer |
| Legacy promotion | `pipeline.py::_ArtifactPromotion` 针对 clip/frame backup、process-local rollback | 不复用为 v2 transaction；它不等价于 content-addressed snapshot + Manifest commit point |
| P2 tests | production factory 直接写 project/registry/manifest fixture；loader tests证明 read-only、containment和selected registry | P2A tests 必须走 production committer；factory 只负责构造 model/payload |
| P2A | 本 task 前没有独立 plan；source/tests/acceptance 仍不存在 | 本 plan 只补 planning artifact，不描述 runtime 已实现 |

## Canonical Ownership

| Contract | Single Owner | Non-Owner Rule |
| --- | --- | --- |
| v2 Pydantic schema | `src/ai_video/production/models.py` | committer 不定义 shadow dataclass schema |
| mutable lifecycle and active pointers | `ProductionManifest` | registry、project snapshot、console、Agent memory 不拥有 status |
| durable writer and recovery | `src/ai_video/production/state_commit.py::ProductionStateCommitter` | loader、registry、P3 adapter 不直接 replace Manifest |
| project semantic hash | existing `hashing.py::canonical_sha256()` / `verify_artifact_hash()` | filename/file SHA 不替代 project semantic hash |
| registry semantic revision | existing `registry.py::registry_semantic_sha256()` | committer 不发明第二种 registry revision |
| file byte evidence | `sha256_file()` or one shared byte helper used by committer and verifier | timestamps/mtime/filename ordering不是 content evidence |
| active project read | Manifest-selected `ProjectSnapshotPointer` | root `project.yaml` 只是合法 entry snapshot/entrypoint，不是第二 active pointer |
| active registry read | Manifest-selected `RegistrySnapshotPointer` | directory scan、highest revision、mtime、lexicographic order 均禁止 |
| writer serialization | `state/commit.lock` held by committer for the whole read-modify-write transaction | process memory lock/Codex session ownership 不算 durable serialization |

## Old Path Decisions

- 不修改 `src/ai_video/manifest.py::{atomic_write_manifest,load_manifest}`；它们继续只拥有 Legacy `RunManifest`。
- 不复用 `src/ai_video/pipeline.py::_ArtifactPromotion`、`_persist_terminal_failure()` 或 `_persist_successful_shot()` 作为 v2 state engine。
- 不让 `production/project.py::load_production_project()` 或 `production/registry.py::load_asset_registry()` 获得 writer、cleanup、activation 或 lifecycle mutation。
- 不让 `tests/production_project_factory.py::write_production_project()` 成为 production commit API 替身。
- 不通过 directory scan、filename sort、mtime 或“最大 revision”推断 active state。
- 不覆盖已存在且 bytes/hash 不同的 immutable snapshot；冲突必须 typed-fail。
- 不在 Manifest replace 后尝试 process-local rollback active pointer。commit point 之后的 uncertain outcome 只能由 restart recovery 判定。
- 不自动删除 complete orphan snapshot；P2A recovery 只报告 orphan。GC/retention 属于 P9 或独立授权。

## Unchanged Contracts

- public CLI 仍只有 `validate`、`run`、`resume`；P2A 不新增命令。
- Legacy default-local ComfyUI、Manifest v1、resume、flat `runs/<run_id>/` layout 和 P1 failure/artifact behavior 全部不变。
- `validate` 保持无副作用；不触发 v2 commit/recovery。
- P2 creative/Shot/Asset Registry domain meaning、content hashes、path containment 和 read-only validation 不被重定义。
- P2A 不实现 P3 Composition/renderer、P4 Audio/Caption、P5 Dependency Graph、P6 QA/repair、P7 image generation、P8 Provider/cloud/paid API 或 P9 GC/retention。
- 不安装 dependency，不联网，不创建 cloud state，不读取 secret。
- content-addressed snapshot hash 不包含 wall-clock timestamp；attempt lifecycle timestamp 只存在 Manifest envelope。

## Storage and Commit Contract

### Active Paths

```text
projects/<project_id>/
├── project.yaml
├── assets/
│   ├── registry.<revision_id>.json
│   └── files/
├── state/
│   ├── commit.lock
│   ├── manifest.json
│   └── projects/
│       └── project.<revision>.<content_hash>.yaml
└── creative/
```

Rules:

1. `project.yaml` remains a valid immutable `ProductionProject` snapshot and stable entrypoint name. It may be selected by the first Manifest.
2. Every subsequently committed project revision uses the versioned path under `state/projects/`.
3. The loader always reads `ProductionManifest.active_project.path`; it never assumes root `project.yaml` is active.
4. The loader always reads `ProductionManifest.active_registry.path`; it never reconstructs the filename from a directory scan.
5. Stored paths are clean, project-relative and contained under their fixed roots.
6. Temporary files are created in the final destination directory with exact owned prefix `.p2a-<attempt_id>-` so rename/link and directory fsync apply to the same filesystem.
7. No temporary or orphan path is stored as active.

### Manifest Shape

`ProductionManifest` remains the only v2 manifest model. Replace the old flat pointer fields; do not keep compatibility aliases:

```python
class ProjectSnapshotPointer(StrictModel):
    path: Path
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RegistrySnapshotPointer(StrictModel):
    path: Path
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class StateCommitStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    OUTCOME_UNKNOWN = "outcome_unknown"


class StateCommitAttempt(StrictModel):
    attempt_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    status: StateCommitStatus
    base_manifest_revision: int = Field(ge=1)
    candidate_project: ProjectSnapshotPointer | None = None
    candidate_registry: RegistrySnapshotPointer | None = None
    started_at: str
    finished_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    project_id: str
    manifest_revision: int = Field(ge=1)
    active_project: ProjectSnapshotPointer
    active_registry: RegistrySnapshotPointer
    attempts: tuple[StateCommitAttempt, ...] = ()
```

Attempt error fields contain only typed code and user-safe message. Raw traceback, secrets, signed URLs and raw provider responses are prohibited.

### Phase Ordering

The committer must expose named phases for injection and receipts:

```python
class CommitPhase(str, Enum):
    AFTER_ATTEMPT_STARTED = "after_attempt_started"
    AFTER_ARTIFACT_TEMP_WRITE = "after_artifact_temp_write"
    AFTER_ARTIFACT_FILE_FSYNC = "after_artifact_file_fsync"
    AFTER_ARTIFACT_PROMOTION = "after_artifact_promotion"
    AFTER_ARTIFACT_DIRECTORY_FSYNC = "after_artifact_directory_fsync"
    AFTER_ARTIFACT_VERIFICATION = "after_artifact_verification"
    AFTER_MANIFEST_TEMP_WRITE = "after_manifest_temp_write"
    AFTER_MANIFEST_FILE_FSYNC = "after_manifest_file_fsync"
    AFTER_MANIFEST_REPLACE = "after_manifest_replace"
    AFTER_MANIFEST_DIRECTORY_FSYNC = "after_manifest_directory_fsync"
```

`AFTER_MANIFEST_REPLACE` 是 logical commit point。它之前失败：old active pointers 必须保持；它之后失败：不得写回 old Manifest，返回 `PRODUCTION_STATE_OUTCOME_UNKNOWN` 并由 recovery 按实际 Manifest bytes 判定。

### Recovery Classification

```python
class RecoveryDisposition(str, Enum):
    ACTIVE = "active"
    PARTIAL_REMOVED = "partial_removed"
    ORPHAN_PRESERVED = "orphan_preserved"
    INTERRUPTED_RECORDED = "interrupted_recorded"


class RecoveryItem(StrictModel):
    path: Path
    disposition: RecoveryDisposition
    sha256: str | None = None


class RecoveryReport(StrictModel):
    manifest_revision_before: int
    manifest_revision_after: int
    items: tuple[RecoveryItem, ...]
```

Recovery rules:

- remove only exact `.p2a-<attempt_id>-*.tmp` files associated with a non-succeeded Manifest attempt;
- never follow symlinks during cleanup;
- preserve and report complete unreferenced content-addressed snapshots;
- convert durable `running`/`outcome_unknown` attempts to `interrupted` only after active Manifest and candidate hashes are inspected;
- if Manifest points to missing/corrupt content, typed-fail; do not guess another revision;
- if final Manifest already selects the candidate, recovery treats the attempt as committed and only clears owned temp residue;
- repeated recovery produces the same active pointers and no additional mutation after the first repaired Manifest.

## Open-Source Fusion Decision

This plan uses `github-oss-fusion` only for structure and tests; no external code is copied:

| Repository | Inspected | Fused | Rejected or Deferred |
| --- | --- | --- | --- |
| [untitaker/python-atomicwrites](https://github.com/untitaker/python-atomicwrites) | README, implementation, tests, MIT license | same-directory temp、file fsync、rename、parent-directory fsync、rollback exception不得覆盖 primary error | repository 已 archived；不新增 dependency，不复制 cross-platform implementation，不接受“所有平台都 power-loss safe”的泛化 claim |
| [git/git](https://github.com/git/git) | `lockfile.c`, ref backend tests, GPL license | lockfile acquire/commit/rollback 分离；pointer update 是显式 commit boundary；失败保留 meaningful errno | GPL code 不复制；不引入 Git refs/objects/repository machinery |
| [sqlite/sqlite](https://github.com/sqlite/sqlite) | pager transaction owner, crash tests, public-domain notice | 按 phase 注入 crash、restart 后验证 old-or-new valid state、commit point 后 outcome 单独分类 | 不引入 SQLite/database/journal/WAL；不复制 C/Tcl implementation |

The fusion is intentionally small: state-machine shape, fsync ordering, exclusive pointer commit and crash-test matrix only.

## Exact File Map

Create:

- `src/ai_video/production/state_commit.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `tests/helpers/p2a_crash_worker.py`

Modify:

- `src/ai_video/production/models.py`
- `src/ai_video/production/project.py`
- `src/ai_video/production/__init__.py`
- `src/ai_video/errors.py`
- `tests/test_production_models.py`
- `tests/test_production_project.py`
- `tests/production_project_factory.py`
- `README.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `docs/agent-primary-contract-matrix.md`

Verify unchanged:

- `src/ai_video/production/hashing.py`
- `src/ai_video/production/paths.py`
- `src/ai_video/production/registry.py`
- `tests/test_production_registry.py`
- `tests/test_production_validation.py`

Do not modify:

- `src/ai_video/{cli,config,models,manifest,pipeline,workflow_loader,workflow_renderer,comfy_client,ffmpeg_tools}.py`
- `tests/test_{cli,config,manifest,pipeline,resume_e2e,workflow_loader,workflow_renderer,ffmpeg_tools}.py`
- `pyproject.toml`
- `configs/**`, `workflows/**`, `runs/**`, `.workflow/**`
- the P3 plan except through a later separately authorized P3 plan revision if accepted P2A API names differ

## Test and Commit Map

| Task | RED Focus | Canonical Owner | Commit |
| --- | --- | --- | --- |
| 0 | authorization/base/schema-layout gate | plan/user decision | no commit |
| 1 | strict pointer/attempt/recovery models and typed errors | `models.py`, `errors.py` | `feat: define production state commit contracts` |
| 2 | deterministic payloads, contained paths and low-level atomic ordering | `state_commit.py` primitives | `feat: add durable production state primitives` |
| 3 | running attempt + immutable artifacts + final Manifest commit | `ProductionStateCommitter` | `feat: commit production state atomically` |
| 4 | phase crash injection and restart recovery | committer recovery | `feat: recover interrupted production state commits` |
| 5 | Manifest-selected reader and production fixtures | `project.py` reader | `feat: load manifest selected production snapshots` |
| 6 | docs, regression, scope and independent review | verification | `docs: document p2a state commit protocol` |

### Task 0: Pass the Implementation and Layout Gates

**Files:**
- Verify: repository Git state and accepted P2 evidence
- Verify: this plan acceptance and explicit P2A runtime authorization

- [ ] **Step 1: Record the exact base and workspace state**

```bash
git status --short --branch
git log --oneline --decorate -12
git show --stat --oneline a5be154
git rev-list --left-right --count origin/main...HEAD
git worktree list --porcelain
```

Expected: accepted P2 is reachable from the chosen base; every unrelated change and active writer is identified before edits.

- [ ] **Step 2: Obtain explicit schema/layout authorization**

The user authorization must name P2A runtime implementation and accept:

```text
ProductionManifest nested active pointers,
state/projects/project.<revision>.<content_hash>.yaml,
state/commit.lock,
Manifest-selected project loading,
POSIX same-filesystem durability boundary,
no automatic orphan deletion.
```

Expected: without this explicit authorization, stop with no source/test/doc modification.

- [ ] **Step 3: Create the implementation lane**

If the current tree is clean and no other writer exists:

```bash
git switch -c feat/p2a-production-state-commit
```

If unrelated work or another writer exists, use a dedicated worktree via `superpowers:using-git-worktrees` instead. Never share one working tree with another write-capable Agent.

- [ ] **Step 4: Record boundaries before implementation**

```text
Problem boundary: v2 project/registry snapshot commit and recovery only.
Single owner: ProductionStateCommitter in production/state_commit.py.
Old path removed: implicit root project.yaml active truth and inferred registry filename.
Unchanged contracts: Legacy CLI/Manifest/pipeline/runs and all P3+ domains.
Focused command: pytest state_commit + state_recovery + project + registry tests.
```

Expected: implementer and reviewers use the same owner/boundary statement.

### Task 1: Define Production State Contracts

**Files:**
- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/errors.py`
- Modify: `src/ai_video/production/__init__.py`
- Modify: `tests/test_production_models.py`

- [ ] **Step 1: Write strict-model RED tests**

Add imports and tests:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production.models import (
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def make_state_manifest() -> ProductionManifest:
    project = ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )
    registry = RegistrySnapshotPointer(
        path=Path(f"assets/registry.{ZERO_HASH}.json"),
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )
    return ProductionManifest(
        project_id="comic-demo",
        manifest_revision=1,
        active_project=project,
        active_registry=registry,
    )


def test_production_manifest_has_one_project_and_registry_pointer_owner():
    manifest = make_state_manifest()
    assert manifest.active_project.path == Path("project.yaml")
    assert manifest.active_registry.revision_id == ZERO_HASH
    assert not hasattr(manifest, "active_project_revision")
    assert not hasattr(manifest, "active_registry_revision")


def test_state_attempt_rejects_unknown_fallback_pointer():
    data = {
        "attempt_id": "attempt-1",
        "operation": "commit_project_registry",
        "status": "running",
        "base_manifest_revision": 1,
        "started_at": "2026-08-09T00:00:00+00:00",
        "fallback_manifest": "state/manifest.backup.json",
    }
    with pytest.raises(ValidationError):
        StateCommitAttempt.model_validate(data)


def test_failed_state_attempt_requires_sanitized_error_fields():
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.FAILED,
            base_manifest_revision=1,
            started_at="2026-08-09T00:00:00+00:00",
            finished_at="2026-08-09T00:00:01+00:00",
        )
```

- [ ] **Step 2: Run schema RED**

```bash
python -m pytest tests/test_production_models.py -q
```

Expected: collection/import fails because P2A pointer/attempt models are absent.

- [ ] **Step 3: Add typed error codes**

Add to `ErrorCode`:

```python
    PRODUCTION_STATE_INVALID = "production_state_invalid"
    PRODUCTION_STATE_BUSY = "production_state_busy"
    PRODUCTION_STATE_COMMIT_FAILED = "production_state_commit_failed"
    PRODUCTION_STATE_RECOVERY_FAILED = "production_state_recovery_failed"
    PRODUCTION_STATE_OUTCOME_UNKNOWN = "production_state_outcome_unknown"
    PRODUCTION_STATE_UNSUPPORTED = "production_state_unsupported"
```

All are non-retryable by default. A higher slice may decide whether a new attempt is safe after recovery; P2A itself does not retry implicitly.

- [ ] **Step 4: Add exact P2A models**

Add the `ProjectSnapshotPointer`, `RegistrySnapshotPointer`, `StateCommitStatus`, `StateCommitAttempt`, `RecoveryDisposition`, `RecoveryItem` and `RecoveryReport` definitions from **Manifest Shape** and **Recovery Classification**. Add validators:

```python
    @field_validator("path")
    @classmethod
    def _require_clean_relative_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("snapshot path must be clean and project-relative")
        return value


    @model_validator(mode="after")
    def _validate_terminal_error(self) -> "StateCommitAttempt":
        terminal_error = self.status in {
            StateCommitStatus.FAILED,
            StateCommitStatus.INTERRUPTED,
            StateCommitStatus.OUTCOME_UNKNOWN,
        }
        if terminal_error and (not self.error_code or not self.error_message):
            raise ValueError("terminal state commit attempts require typed error fields")
        if self.status is StateCommitStatus.SUCCEEDED and self.finished_at is None:
            raise ValueError("succeeded state commit attempts require finished_at")
        return self


    @model_validator(mode="after")
    def _validate_unique_attempt_ids(self) -> "ProductionManifest":
        attempt_ids = [item.attempt_id for item in self.attempts]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("Production Manifest attempt IDs must be unique")
        return self
```

Apply the clean-path validator to both pointer models. Add a `RegistrySnapshotPointer` model validator requiring `revision_id == content_hash`. Replace the three flat active fields in `ProductionManifest` with `manifest_revision`, `active_project`, `active_registry` and immutable `attempts`. Do not retain deprecated properties or aliases.

- [ ] **Step 5: Export stable P2A model entry points**

Update `production/__init__.py` to export the pointer, attempt and recovery models. Do not export the writer until Task 3 GREEN.

- [ ] **Step 6: Run GREEN and commit**

```bash
python -m pytest tests/test_production_models.py tests/test_errors.py -q
git add src/ai_video/production/models.py src/ai_video/production/__init__.py \
  src/ai_video/errors.py tests/test_production_models.py
git commit -m "feat: define production state commit contracts"
```

Expected: strict/frozen/extra-forbid tests pass; no Legacy model changes.

### Task 2: Add Durable Atomic Primitives

**Files:**
- Create: `src/ai_video/production/state_commit.py`
- Create: `tests/test_production_state_commit.py`

- [ ] **Step 1: Write RED tests for ordering and containment**

Create tests around an injected file-operations recorder:

```python
def test_atomic_manifest_write_orders_file_and_directory_durability(tmp_path):
    ops = RecordingFileOps()
    writer = make_committer(tmp_path, ops=ops)
    writer._write_manifest_atomic(make_state_manifest())
    assert ops.events == [
        "write:state/.p2a-manifest.tmp",
        "flush:state/.p2a-manifest.tmp",
        "fsync_file:state/.p2a-manifest.tmp",
        "replace:state/.p2a-manifest.tmp->state/manifest.json",
        "fsync_dir:state",
    ]


def test_prepared_artifact_rejects_reserved_manifest_target(tmp_path):
    writer = make_committer(tmp_path)
    with pytest.raises(AiVideoError) as exc:
        writer.prepare_artifact(
            attempt_id="attempt-1",
            relative_path=Path("state/manifest.json"),
            payload=b"forbidden",
        )
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_prepared_artifact_rejects_symlink_parent(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "state").symlink_to(outside, target_is_directory=True)
    writer = make_committer(tmp_path)
    with pytest.raises(AiVideoError, match="symlink"):
        writer.prepare_artifact(
            attempt_id="attempt-1",
            relative_path=Path("state/projects/project.2.yaml"),
            payload=b"project",
        )
```

- [ ] **Step 2: Run primitive RED**

```bash
python -m pytest tests/test_production_state_commit.py -q
```

Expected: collection fails because `ProductionStateCommitter` and test helpers do not exist.

- [ ] **Step 3: Add request and injection interfaces**

Define in `state_commit.py`:

```python
@dataclass(frozen=True)
class PreparedArtifact:
    relative_path: Path
    payload: bytes
    file_sha256: str


@dataclass(frozen=True)
class StateCommitRequest:
    attempt_id: str
    operation: str
    expected_manifest_revision: int
    artifacts: tuple[PreparedArtifact, ...]
    next_project: ProjectSnapshotPointer
    next_registry: RegistrySnapshotPointer


class CrashInjector(Protocol):
    def checkpoint(self, phase: CommitPhase) -> None:
        raise NotImplementedError


class NoopCrashInjector:
    def checkpoint(self, phase: CommitPhase) -> None:
        return None
```

`prepare_artifact()` calculates `hashlib.sha256(payload).hexdigest()` itself. Caller-provided hashes are evidence to compare, never trusted substitutes.

- [ ] **Step 4: Add exact path and serialization helpers**

Implement:

```python
_RESERVED_TARGETS = {
    Path("state/manifest.json"),
    Path("state/commit.lock"),
}


def _owned_temp_name(attempt_id: str, final_path: Path) -> str:
    safe_attempt = re.sub(r"[^A-Za-z0-9_-]", "_", attempt_id)
    return f".p2a-{safe_attempt}-{final_path.name}.tmp"


def _canonical_json_bytes(model: BaseModel) -> bytes:
    payload = json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _canonical_yaml_bytes(model: BaseModel) -> bytes:
    payload = yaml.safe_dump(
        model.model_dump(mode="json"),
        sort_keys=True,
        allow_unicode=True,
    )
    return payload.encode("utf-8")
```

Reject absolute paths, `..`, reserved targets, `runs/**`, `.workflow/**`, any symlink component and final paths outside resolved project root. Temp path must share the final parent directory.

- [ ] **Step 5: Add POSIX lock and atomic file operations**

Use `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on persistent `state/commit.lock`. Hold the fd from initial Manifest read through final cleanup. If `fcntl` is unavailable, raise `PRODUCTION_STATE_UNSUPPORTED`; if lock acquisition would block, raise `PRODUCTION_STATE_BUSY`.

Atomic mutable write order is exactly:

```python
with temp_path.open("xb") as handle:
    handle.write(payload)
    handle.flush()
    os.fsync(handle.fileno())
os.replace(temp_path, final_path)
_fsync_directory(final_path.parent)
```

Immutable promotion must not overwrite:

```python
try:
    os.link(temp_path, final_path)
except FileExistsError:
    if sha256_file(final_path) != expected_sha256:
        raise _state_commit_failed("Immutable snapshot path already has different bytes.")
else:
    _fsync_directory(final_path.parent)
finally:
    temp_path.unlink(missing_ok=True)
```

Verify `temp_path.stat().st_dev == final_path.parent.stat().st_dev` before promotion. Preserve the primary exception if cleanup also fails by using `exc.add_note()`.

- [ ] **Step 6: Run GREEN and commit**

```bash
python -m pytest tests/test_production_state_commit.py -q
git add src/ai_video/production/state_commit.py tests/test_production_state_commit.py
git commit -m "feat: add durable production state primitives"
```

Expected: ordering, lock, path, symlink, collision and cleanup tests pass without network or new dependency.

### Task 3: Commit Project and Registry State

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `src/ai_video/production/__init__.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Upgrade the shared fixture to the P2A Manifest shape**

Keep the current `write_production_project(root)` model construction unchanged. Replace only its final project/registry/Manifest write block with exact pointer construction:

```python
    project_path = root / "project.yaml"
    _write_yaml(project_path, project)
    registry_path = root / f"assets/registry.{registry.revision_id}.json"
    registry_payload = (
        json.dumps(
            registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    manifest = ProductionManifest(
        project_id=project.project_id,
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=sha256_file(project_path),
        ),
        active_registry=RegistrySnapshotPointer(
            path=registry_path.relative_to(root),
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=sha256_file(registry_path),
        ),
    )
    manifest_path = root / "state/manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return project_path
```

Add `make_revision_two_request(root)` by loading the current committed fixture, creating a sealed revision-2 `ProductionProject`, creating its exact registry snapshot, and calling `prepare_project_registry_commit()`; it must not hand-build a second request/pointer algorithm. The initial fixture may write state directly for read-only loader tests, but every update/activation test must call `ProductionStateCommitter`.

- [ ] **Step 2: Write transaction RED tests**

Add tests proving the active pointer changes only at the final Manifest replace:

```python
@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_ATTEMPT_STARTED,
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
    ],
)
def test_failure_before_manifest_replace_preserves_old_active_pointers(
    committed_project, phase
):
    before = read_manifest(committed_project)
    committer = make_committer(
        committed_project,
        injector=RaisingCrashInjector(phase),
    )
    with pytest.raises(AiVideoError):
        committer.commit(make_revision_two_request(committed_project))
    after = read_manifest(committed_project)
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry


def test_success_switches_both_pointers_in_one_manifest_revision(committed_project):
    before = read_manifest(committed_project)
    result = make_committer(committed_project).commit(
        make_revision_two_request(committed_project)
    )
    after = read_manifest(committed_project)
    assert after.manifest_revision == before.manifest_revision + 2
    assert after.active_project == result.active_project
    assert after.active_registry == result.active_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED
```

The revision increases twice: once for durable `running`, once for final `succeeded` pointer commit.

- [ ] **Step 3: Run transaction RED**

```bash
python -m pytest tests/test_production_state_commit.py -q
```

Expected: new tests fail because `commit()` is absent.

- [ ] **Step 4: Build exact project and registry candidates**

Add public helper:

```python
def prepare_project_registry_commit(
    *,
    manifest: ProductionManifest,
    project: ProductionProject,
    registry: AssetRegistrySnapshot,
    attempt_id: str,
) -> StateCommitRequest:
    if project.project_id != manifest.project_id:
        raise _state_invalid("Project ID does not match Production Manifest.")
    if not verify_artifact_hash(project):
        raise _state_invalid("Project semantic content hash is invalid.")
    registry_hash = registry_semantic_sha256(registry)
    if registry.revision_id != registry.content_hash or registry.content_hash != registry_hash:
        raise _state_invalid("Registry revision and semantic content hash are invalid.")
    if project.revision < manifest.active_project.revision:
        raise _state_invalid("Project revision cannot move backwards.")
    if (
        project.revision == manifest.active_project.revision
        and project.content_hash != manifest.active_project.content_hash
    ):
        raise _state_invalid("A project revision cannot be reused with different content.")

    project_payload = _canonical_yaml_bytes(project)
    registry_payload = _canonical_json_bytes(registry)
    project_path = Path(
        f"state/projects/project.{project.revision}.{project.content_hash}.yaml"
    )
    registry_path = Path(f"assets/registry.{registry.revision_id}.json")
    project_file_hash = hashlib.sha256(project_payload).hexdigest()
    registry_file_hash = hashlib.sha256(registry_payload).hexdigest()
    return StateCommitRequest(
        attempt_id=attempt_id,
        operation="commit_project_registry",
        expected_manifest_revision=manifest.manifest_revision,
        artifacts=(
            PreparedArtifact(project_path, project_payload, project_file_hash),
            PreparedArtifact(registry_path, registry_payload, registry_file_hash),
        ),
        next_project=ProjectSnapshotPointer(
            path=project_path,
            revision=project.revision,
            content_hash=project.content_hash,
            file_sha256=project_file_hash,
        ),
        next_registry=RegistrySnapshotPointer(
            path=registry_path,
            revision_id=registry.revision_id,
            content_hash=registry.content_hash,
            file_sha256=registry_file_hash,
        ),
    )
```

It must:

1. require `project.project_id == manifest.project_id`;
2. require `verify_artifact_hash(project)`;
3. require `registry.revision_id == registry.content_hash == registry_semantic_sha256(registry)`;
4. serialize project YAML and registry canonical JSON once;
5. set project path to `state/projects/project.<revision>.<content_hash>.yaml`;
6. set registry path to `assets/registry.<revision_id>.json`;
7. calculate exact byte hashes for both pointers;
8. reject a reused revision with different semantic content; allow identical semantic content to migrate the initial root snapshot to its content-addressed path.

- [ ] **Step 5: Implement the single commit state machine**

`ProductionStateCommitter.commit(request)` must:

1. acquire the project lock;
2. read and validate current Manifest;
3. compare `manifest_revision` with `expected_manifest_revision`;
4. reject reused `attempt_id` with different candidate hashes;
5. atomically persist a `running` attempt without changing active pointers;
6. write/fsync/promote/fsync/verify all immutable artifacts in sorted request order;
7. reopen project/registry through their existing domain verifiers;
8. build one final Manifest selecting both exact pointers and marking attempt `succeeded`;
9. write/fsync/replace/fsync final Manifest;
10. return the reloaded Manifest.

On a caught failure before Manifest replace, atomically persist `failed` with sanitized error and unchanged pointers. If persisting `failed` also fails, preserve the original exception and add the persistence failure as a note.

After `AFTER_MANIFEST_REPLACE`, any failure becomes `PRODUCTION_STATE_OUTCOME_UNKNOWN`; do not write another Manifest in the same process.

- [ ] **Step 6: Prove generic future artifact staging remains bounded**

Add tests that `PreparedArtifact` can carry an arbitrary contained future path such as `composition/source.<hash>.json`, but cannot carry:

```text
state/manifest.json
state/commit.lock
runs/run-1/manifest.json
../outside
an absolute path
a symlink-escaped parent
```

The committer owns bytes and durability only. It does not validate Composition/Audio/Provider domain semantics and cannot activate a field absent from `ProductionManifest`.

- [ ] **Step 7: Export the approved API**

Export only:

```python
ProductionStateCommitter
PreparedArtifact
StateCommitRequest
prepare_project_registry_commit
```

Do not export raw `_write_manifest_atomic()`, lock or cleanup helpers. Export `recover_production_state` only after Task 4 GREEN defines it.

- [ ] **Step 8: Run GREEN and commit**

```bash
python -m pytest tests/test_production_state_commit.py \
  tests/test_production_project.py tests/test_production_registry.py -q
git add src/ai_video/production/state_commit.py src/ai_video/production/__init__.py \
  tests/test_production_state_commit.py tests/production_project_factory.py
git commit -m "feat: commit production state atomically"
```

Expected: exact pointer ordering and idempotency pass; no Legacy file changes.

### Task 4: Recover Interrupted Commits

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Create: `tests/test_production_state_recovery.py`
- Create: `tests/helpers/p2a_crash_worker.py`

- [ ] **Step 1: Add a real subprocess crash worker**

Create a helper whose only job is to invoke one commit and terminate at an injected phase:

```python
from __future__ import annotations

import os
import sys
from pathlib import Path

from ai_video.production.state_commit import CommitPhase, ProductionStateCommitter

TESTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS_DIR))

from production_project_factory import make_revision_two_request


class ExitInjector:
    def __init__(self, target: CommitPhase) -> None:
        self.target = target

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.target:
            os._exit(91)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    phase = CommitPhase(sys.argv[2])
    request = make_revision_two_request(root)
    ProductionStateCommitter(root, injector=ExitInjector(phase)).commit(request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The production module receives only an injected protocol. It must not read a crash-test environment variable.

- [ ] **Step 2: Write restart RED tests for every phase**

```python
@pytest.mark.parametrize("phase", tuple(CommitPhase))
def test_restart_after_process_crash_has_one_valid_active_state(
    committed_project, phase
):
    before = load_production_project(committed_project / "project.yaml")
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91
    report = recover_production_state(committed_project)
    after = load_production_project(committed_project / "project.yaml")
    assert after.manifest.active_project in {
        before.manifest.active_project,
        revision_two_project_pointer(committed_project),
    }
    assert after.manifest.active_registry in {
        before.manifest.active_registry,
        revision_two_registry_pointer(committed_project),
    }
    assert pointers_form_one_committed_pair(after.manifest)
    assert report.manifest_revision_after >= report.manifest_revision_before
```

Do not accept a mixed old-project/new-registry pair.

- [ ] **Step 3: Add focused recovery RED cases**

Cover:

```python
def test_recovery_removes_only_owned_partial_temp(committed_project):
    owned = make_owned_partial(committed_project, "attempt-2")
    unrelated = committed_project / "assets/.user-file.tmp"
    unrelated.write_bytes(b"preserve")
    report = recover_production_state(committed_project)
    assert not owned.exists()
    assert unrelated.read_bytes() == b"preserve"
    assert any(item.disposition is RecoveryDisposition.PARTIAL_REMOVED for item in report.items)


def test_recovery_preserves_complete_orphan(committed_project):
    orphan = write_complete_orphan_project_snapshot(committed_project)
    report = recover_production_state(committed_project)
    assert orphan.is_file()
    assert any(
        item.path == orphan.relative_to(committed_project)
        and item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
        for item in report.items
    )


def test_recovery_refuses_corrupt_active_snapshot(committed_project):
    corrupt_active_project(committed_project)
    with pytest.raises(AiVideoError) as exc:
        recover_production_state(committed_project)
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
```

- [ ] **Step 4: Implement deterministic recovery**

`recover_production_state(root)` must acquire the same lock, load the active Manifest, verify both active snapshots and classify every incomplete attempt. It may write one repaired Manifest only when converting `running`/`outcome_unknown` to `interrupted` or `succeeded` based on exact selected pointers.

It must not:

- delete complete orphan content;
- choose an orphan as active;
- follow symlinks;
- scan outside the exact project snapshot/registry/temp namespaces;
- infer a transaction from mtime;
- call Legacy resume or Manifest helpers.

- [ ] **Step 5: Run crash GREEN repeatedly**

```bash
python -m pytest tests/test_production_state_recovery.py -q
python -m pytest tests/test_production_state_recovery.py -q
python -m pytest tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected: all phases yield one valid old-or-new committed pair; repeated recovery is idempotent and produces no additional snapshot/Manifest mutation.

- [ ] **Step 6: Export the recovery entry point**

Add `recover_production_state` to `production/__init__.py` only after the recovery tests pass. Keep recovery explicit; `load_production_project()` must not invoke it automatically.

- [ ] **Step 7: Commit recovery**

```bash
git add src/ai_video/production/state_commit.py src/ai_video/production/__init__.py \
  tests/test_production_state_recovery.py tests/helpers/p2a_crash_worker.py
git commit -m "feat: recover interrupted production state commits"
```

### Task 5: Load Manifest-Selected Snapshots

**Files:**
- Modify: `src/ai_video/production/project.py`
- Modify: `tests/production_project_factory.py`
- Modify: `tests/test_production_project.py`
- Verify: `src/ai_video/production/registry.py`
- Verify: `tests/test_production_registry.py`

- [ ] **Step 1: Confirm every update fixture uses the canonical committer**

Search before adding reader tests:

```bash
rg -n "active_project|active_registry|manifest_revision" tests/production_project_factory.py \
  tests/test_production_project.py tests/test_production_state_*.py
```

Expected: direct initial-state construction exists only in `write_production_project()`; every revision update calls `prepare_project_registry_commit()` and `ProductionStateCommitter.commit()`.

- [ ] **Step 2: Write reader RED tests**

```python
def test_loader_reads_manifest_selected_project_snapshot(tmp_path):
    project_path = write_production_project(tmp_path)
    commit_revision_two(tmp_path)
    root_entry = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    loaded = load_production_project(project_path)
    assert root_entry["revision"] == 1
    assert loaded.project.revision == 2
    assert loaded.manifest.active_project.path.name.startswith("project.2.")


def test_loader_does_not_select_decoy_project_snapshot(tmp_path):
    project_path = write_production_project(tmp_path)
    decoy = (
        tmp_path
        / "state/projects"
        / f"project.999.{'f' * 64}.yaml"
    )
    decoy.parent.mkdir(parents=True, exist_ok=True)
    decoy.write_text("not: valid", encoding="utf-8")
    loaded = load_production_project(project_path)
    assert loaded.project.revision == loaded.manifest.active_project.revision


def test_loader_rejects_manifest_selected_project_hash_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    selected = selected_project_snapshot(tmp_path)
    selected.write_text("tampered: true\n", encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
```

- [ ] **Step 3: Update the read-only loader**

Change `load_production_project()` so the supplied `project.yaml` resolves only the project root/entrypoint. Then:

1. load `state/manifest.json`;
2. resolve `manifest.active_project.path` under allowed roots `project_root` or `state/projects`;
3. require project pointer revision/hash/file hash to match loaded file/model;
4. resolve `manifest.active_registry.path` under `assets`;
5. require registry pointer revision/content/file hash to match `load_asset_registry()` result;
6. continue existing creative, asset and cross-reference validation.

Do not call recovery automatically from the loader. Recovery is an explicit write-capable operation; a read-only load of inconsistent state must typed-fail.

- [ ] **Step 4: Run focused reader/registry GREEN**

```bash
python -m pytest tests/test_production_project.py \
  tests/test_production_registry.py tests/test_production_validation.py -q
```

Expected: selected exact paths load; decoys, traversal, symlink escape and hash mismatch fail; loader remains side-effect free.

- [ ] **Step 5: Commit reader integration**

```bash
git add src/ai_video/production/project.py tests/production_project_factory.py \
  tests/test_production_project.py
git commit -m "feat: load manifest selected production snapshots"
```

### Task 6: Document, Regress and Review P2A

**Files:**
- Modify: `README.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `docs/agent-primary-contract-matrix.md`
- Verify: all P2A/P2/Legacy files

- [ ] **Step 1: Run the focused P2A/P2 suite**

```bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected: all P2/P2A tests pass; no network, renderer, Provider or optional dependency.

- [ ] **Step 2: Run Legacy regression**

```bash
python -m pytest tests/test_config.py tests/test_cli.py tests/test_manifest.py \
  tests/test_pipeline.py tests/test_resume_e2e.py -q
```

Expected: Legacy CLI/Manifest/resume/layout behavior remains unchanged.

- [ ] **Step 3: Run the full default suite**

```bash
python -m pytest -q
```

Expected: full suite passes; only the repository's already-known optional skip may remain. Record exact pass/skip counts instead of copying old P2 counts.

- [ ] **Step 4: Update runtime-truth docs**

Only after code/tests pass:

- README: describe P2A as internal v2 state infrastructure, not a new CLI.
- runtime baseline: list exact implemented files/models and POSIX/same-filesystem durability boundary.
- roadmap: mark P2A implemented/accepted only after independent review; update P3 execution prerequisite accordingly.
- contract matrix: add canonical P2A owner, forbidden Legacy paths and focused commands.
- remove stale “P2 integration pending” wording only where directly necessary to state the verified P2A base; do not perform unrelated editorial cleanup.

- [ ] **Step 5: Commit docs**

```bash
git add README.md docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md docs/agent-primary-contract-matrix.md
git commit -m "docs: document p2a state commit protocol"
```

- [ ] **Step 6: Run scope and claim scans**

```bash
git diff --check
git status --short --branch
p2a_base_commit=$(git merge-base HEAD main)
git diff --name-only "$p2a_base_commit"..HEAD
rg -n "hyperframes|remotion|elevenlabs|captions|httpx|requests|runs/" \
  src/ai_video/production tests/test_production_*.py \
  tests/helpers/p2a_crash_worker.py
rg -n "byte-identical|all platforms|zero data loss|power-loss safe" \
  README.md docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md docs/agent-primary-contract-matrix.md
```

Expected: only exact file map changed; external-domain terms appear only in denial/boundary text; docs do not overclaim portability or absolute power-loss guarantees.

- [ ] **Step 7: Obtain independent spec review**

Review brief:

```text
Verdict must be accept, accept with concerns, or reject.
Verify ProductionManifest is the only mutable lifecycle and active pointer owner.
Verify state_commit.py is the only v2 writer/recovery owner.
Verify active project and registry are selected by exact Manifest paths/hashes.
Verify running attempt is durable before material work.
Verify immutable artifacts are file-fsynced, promoted without overwrite, directory-fsynced and reverified.
Verify final Manifest replace is the single commit point and its directory is fsynced.
Verify crash phases produce one valid old-or-new project/registry pair after recovery.
Verify partial temp cleanup is owned and bounded; complete orphan snapshots are preserved/reported.
Verify no loader/registry/Legacy second writer, no implicit directory selection and no automatic rollback after commit point.
Verify no P3+ domain, new CLI, dependency, network, Provider, Legacy schema/layout or GC implementation entered scope.
Verify tests cover collision, symlink escape, lock contention, manifest revision conflict, idempotency and uncertain outcome.
```

Required verdict: `accept` or `accept with concerns` with no blocking issue. The parent must directly verify every blocking claim and final diff.

- [ ] **Step 8: Obtain independent code-quality review**

Review the accepted spec-compliant diff for:

- exception preservation and sanitized persisted error fields;
- minimal public API and no future-domain coupling;
- duplicated hash/path/Manifest logic;
- fd/temp cleanup on every branch;
- deterministic tests without timing sleeps;
- production files remaining under 800 lines where practical.

Required verdict: approved with no unresolved important issue.

- [ ] **Step 9: Record final branch truth**

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
```

Expected: clean feature branch/worktree and explicit local-vs-origin state. Do not claim merge, push, release or P3 readiness without corresponding evidence.

## Failure and Rollback

### Runtime Failure Rules

- failure before durable `running`: no attempt claim and no artifact mutation;
- failure after durable `running` but before final Manifest replace: old active pointers remain; synchronous failure records `failed`, crash recovery records `interrupted`;
- immutable promotion collision with different bytes: typed integrity failure; never overwrite;
- active Manifest revision mismatch: typed conflict; caller must reload and rebuild request;
- Manifest replace failure: old Manifest remains active;
- failure after Manifest replace: `outcome_unknown`; do not roll back in-process; restart recovery decides from exact Manifest bytes;
- corrupt active snapshot: recovery fails closed and never guesses an orphan;
- partial owned temp: safe bounded cleanup;
- complete orphan: preserved and reported; no automatic GC;
- lock contention: typed busy failure; no waiting loop or retry storm;
- non-POSIX environment: typed unsupported failure before write.

### Code Rollback

Revert implementation commits in reverse order:

```bash
git revert "$(git log -1 --format=%H --grep='^docs: document p2a state commit protocol$')"
git revert "$(git log -1 --format=%H --grep='^feat: load manifest selected production snapshots$')"
git revert "$(git log -1 --format=%H --grep='^feat: recover interrupted production state commits$')"
git revert "$(git log -1 --format=%H --grep='^feat: commit production state atomically$')"
git revert "$(git log -1 --format=%H --grep='^feat: add durable production state primitives$')"
git revert "$(git log -1 --format=%H --grep='^feat: define production state commit contracts$')"
```

Do not delete `projects/**`, immutable snapshots, manifests, or user artifacts during rollback. After rollback, P2A-created state is unsupported but preserved for manual recovery. Any schema downgrade/migration or orphan GC requires a separate authorized tool/plan.

## Acceptance Criteria

P2A is accepted only when:

1. accepted P2 is the implementation base;
2. `ProductionManifest` is the only active project/registry and attempt-state owner;
3. `ProductionStateCommitter` is the only v2 writer/recovery owner;
4. no flat/nested duplicate pointer control plane remains;
5. root `project.yaml` is not implicitly treated as active after Manifest selects a versioned snapshot;
6. project/registry paths and both semantic/file hashes are persisted and reverified;
7. attempt `running` is durable before material work;
8. immutable files are temp-written, file-fsynced, promoted without overwrite, parent-directory-fsynced and reopened before activation;
9. final Manifest temp is file-fsynced, atomically replaced and state directory is fsynced;
10. final Manifest replace is the single commit point;
11. pre-commit failures preserve old active pointers;
12. post-replace uncertain outcomes are resolved only through restart recovery;
13. real subprocess crash injection covers every named phase;
14. recovery yields one valid old-or-new project/registry pair, never a mixed pair;
15. owned partial temps are cleaned without following symlinks or deleting unrelated files;
16. complete orphan snapshots remain unselected, preserved and reported;
17. corrupt active state fails closed without directory/mtime/revision guessing;
18. writer lock and expected Manifest revision prevent silent concurrent lost updates on the supported POSIX target;
19. P2 readers remain side-effect free and registry hash owner is reused;
20. no Legacy writer/pipeline/layout behavior changes;
21. no renderer, Audio/Caption, Dependency Graph, Provider/cloud/paid API, new CLI, dependency, migration tool or GC enters scope;
22. focused P2A/P2, Legacy regression and full default suites pass;
23. docs state only verified POSIX/same-filesystem guarantees;
24. independent spec and code-quality reviews have no blocker.

## Plan-Time Known Gates

- **Plan drafting:** authorized by the user's choice `A`; no blocker.
- **P2A runtime execution:** not authorized by this docs-only planning turn; requires explicit implementation and schema/layout authorization.
- **Platform:** first implementation targets POSIX local filesystem. Broader Windows/network-filesystem guarantees require a separate compatibility plan and real fault testing.
- **P3:** remains blocked until P2A implementation passes crash-injection tests and independent acceptance. If accepted P2A public paths/symbols differ from the committed P3 plan, revise and re-review P3 before execution.
- **GC/retention:** complete orphan deletion remains deferred; recovery only reports it.
- **Documentation state:** commit `f600ca2` 已将 P2 truth 对齐为 accepted on local `main`，并将 P2A/P3 标为 planning-only。Implementation docs 只在验证完成后更新 P2A runtime status，不再重复清理已解决的 P2 wording。

## Final Authorization Boundary

Creating and committing this plan grants no authority to modify `src/**` or tests, change the Production Manifest schema/layout, create a feature branch/worktree, execute crash workers, or implement P2A. Before Task 0 Step 3 or any runtime edit, the user must explicitly authorize P2A implementation and the schema/layout/platform decisions listed in **Execution Authorization Gate**. P3 must remain stopped until P2A is implemented, independently reviewed and accepted.
