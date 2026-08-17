# ProductionStateCommitter Responsibility Split Specification

Status: Approved design for a behavior-preserving internal refactor. 本文件授权的目标仅是拆分 `src/ai_video/production/state_commit.py` 的实现职责；不授权修改 public API、schema、persistence layout、CLI contract、transaction semantics 或 recovery semantics。

Planning snapshot: 2026-08-17。设计时 `state_commit.py` 约 7,300 physical LOC，`ProductionStateCommitter` 仍是 v2 production state write、activation 与 explicit recovery 的唯一 owner。拆分必须降低该文件的 architecture debt，同时保持这个 single-writer contract。

## 1. Goal

把当前集中在 `state_commit.py` 的多个 domain lifecycle 提取到少量 private、按职责聚合的 implementation modules，同时保留一个 public façade：

```text
callers
  -> ProductionStateCommitter façade
  -> private domain mixin
  -> shared transaction and persistence primitives
  -> one durable production-state activation
```

本次拆分必须做到：

- `ProductionStateCommitter` 继续是唯一可实例化 writer/recovery owner；
- correctness-critical transaction lifecycle 保持完整，不为追求小文件机械切断 invariant；
- 原有 imports、method signatures、error mapping、crash checkpoints 与 test seams 保持兼容；
- private implementation dependency direction 单向、无新 cycle；
- Architecture Gate baseline 在行为验证完成后显式更新，记录减少后的 debt，而不是扩大豁免。

## 2. Non-Goals

- 不改变业务行为、public API、Manifest/Registry/Graph schema 或 artifact layout。
- 不改变 Legacy CLI、P2 reader、P3/P4 renderer、P5 dependency semantics 或 P6 review/repair semantics。
- 不增加 writer、repository、service container 或通用 transaction framework。
- 不把 transaction 的每一步拆成独立 class/file。
- 不清理无关历史代码，不新增 runtime dependency。

## 3. Current Contract and Invariants

### 3.1 Sole owner

`ProductionStateCommitter` 当前同时承载 project/registry commit、dependency transition、voice lifecycle、render lifecycle、review/repair/final acceptance 与 explicit recovery。拆分后，这些实现可以位于 private modules，但 ownership 语义不变：所有 state mutation 仍必须经同一个 façade instance、同一个 project root、同一个 file-ops adapter 与同一把 exclusive lock。

P2 reader、registry、validation、dependency graph builder、Provider adapter 和 renderer 均不得获得独立写入能力。

### 3.2 Transaction integrity

以下顺序和 crash semantics 必须保持：

```text
lock
  -> validate exact base state
  -> write owned candidate/temp
  -> fsync candidate and parent
  -> promote immutable evidence
  -> reopen and verify durable bytes
  -> replace the authoritative manifest
  -> fsync parent
  -> explicit recovery under the same lock when required
```

`_commit_locked()`、render activation、voice submit/candidate/activation 和 recovery attempt classification 等不可分割 lifecycle 可以超过普通模块大小建议；应按 invariant 边界移动为整体，不能为满足 LOC 数字重排步骤。

### 3.3 Compatibility surface

必须保留：

- `ai_video.production` 当前 re-export 的 request/result types、prepare functions、`ProductionStateCommitter` 和 `recover_production_state`；
- 直接从 `ai_video.production.state_commit` import 的 `CommitPhase`、crash injector types、voice/render attempt types、prepare helpers 与 durable permit typing surface；
- 现有测试使用的 `_NativeFileOps`、canonical serialization/hash/path helpers；
- module-global和 instance-level monkeypatch seams，包括 loaders、`fcntl`、selected `os` operations、`_NativeFileOps` methods、`_write_*_atomic`、recovery temp/hash helpers，以及 current render/timeline readers；
- `CommitPhase` value、checkpoint order、typed error code/message、exit behavior 和 exact path naming。

## 4. Selected Architecture

选择 private domain mixins + sole public façade。Composition service 方案会引入多个持有 committer state 的协作者并扩大 transaction migration 风险；只提取 pure helpers 又无法实质降低当前 God Module debt。

### 4.1 Public façade

`src/ai_video/production/state_commit.py` 保留：

- `ProductionStateCommitter` 的 public identity、constructor、`project_root` 和 lock entry；
- public/direct compatibility re-exports；
- patch-sensitive loader wrappers 与 `fcntl` lock seam；
- mixin composition order；
- 必要的薄 dispatch，不承载完整 domain lifecycle。

Façade 不复制 mutable domain state。唯一 instance state 继续是当前 project root、file operations、crash injector 与已存在的 injected collaborators。

### 4.2 Private modules

使用 leading underscore 表示非 public contract。最终文件数量以实际 cohesion 为准，目标边界为：

```text
_state_commit_contracts.py
  request/result dataclasses, protocols, CommitPhase and crash seams

_state_commit_prepare.py
  pure candidate preparation, canonical hashes and path derivation

_state_commit_review.py
_state_commit_repair.py
  review, repair and final-acceptance lifecycles

_state_commit_voice_intent.py
_state_commit_voice_candidate.py
_state_commit_voice_activation.py
  durable voice intent/permit, candidate preparation and activation

_state_commit_render_lifecycle.py
_state_commit_render_support.py
  render attempt/activation transaction and supporting validation/persistence

_state_commit_dependency.py
  dependency lifecycle mutation methods

_state_commit_recovery.py
_state_commit_recovery_attempts.py
_state_commit_recovery_fs.py
  recovery orchestration, exact old/new attempt reasoning and safe filesystem handling

_state_commit_transaction.py
_state_commit_persistence.py
  core commit transaction plus shared atomic/path/file-descriptor primitives
```

实现时允许合并自然较小且高度相关的候选模块。禁止为了目录外观制造只有一个 trivial function 的文件。新 production modules 以约 800 effective LOC 为目标；不可分割 transaction invariant 优先于机械行数限制。

### 4.3 Dependency direction

```text
state_commit façade
  -> domain mixins
  -> contracts / prepare / persistence primitives
  -> existing production models, validation, registry and dependency readers
```

Private modules不得 runtime import `state_commit.py`。Shared primitives不得 import domain mixins。跨 mixin 调用继续通过 `self._method()` late binding，使现有 instance monkeypatch 与 subclass/test seam 生效，同时避免引入 service registry。

## 5. Data and Control Flow

### 5.1 Normal mutation

1. Caller 通过原有 API 调用 façade method。
2. Façade或 mixin 取得原有 exclusive project lock。
3. Domain mixin验证 exact active state、request identity 与 lifecycle transition。
4. Mixin 调用同一 instance 上的 prepare/persistence helpers。
5. Immutable evidence完成 write、`fsync`、promotion 与 reopen verification。
6. 只有 authoritative Manifest replace 构成 activation point。
7. 原有 typed result 或 typed error 返回 caller。

模块边界不得在步骤 3–6 之间建立新的 durable owner，也不得缓存 active state。

### 5.2 Voice and render

Voice 的 durable intent、one-use permit、Provider submission、candidate 与 activation顺序保持现状。Render 的 begin/failure/activation lifecycle 继续把 Composition、ResolvedTimeline、renderer source 与 final render evidence作为同一次 activation处理。

提取时移动完整 method body，除 import/name binding 所需调整外不重写条件分支。

### 5.3 Recovery

`recover_production_state()` 仍是 explicit API。它通过 façade在同一 lock 下调用 recovery mixins；recovery 只删除 committer-owned temp，保留无法证明 ownership 的 orphan，并保持 existing old/new hash reasoning、unknown-outcome mapping 和 idempotency。

## 6. Compatibility Strategy

- Dataclass/protocol/enum 可以定义在 `_state_commit_contracts.py`，但必须由 `state_commit.py` re-export，保持 import path。
- Patch-sensitive globals不在提取时静态捕获。Moved methods通过 façade wrapper 或 `self` method读取 `load_production_project`、`load_verified_render_state` 等 bindings，使 monkeypatch仍作用于原位置。
- `_NativeFileOps` 只定义一次并从 façade re-export，保持 class identity与 method monkeypatch。
- `fcntl` acquisition保留在 façade；共享的 `os` module object与 selected file-op seams保持可观察行为。
- 不改变 exception wrapping层级；既有 `AiVideoError`、`ErrorCode`、reason text与 commit-point mapping是 regression contract。

## 7. Implementation Sequence

采用 behavior-preserving、可逐波回归的机械迁移：

1. 增加 structural contract test，先证明当前 façade oversized/未拆分状态为 RED，并锁定 import、re-export 与 acyclic dependency要求。
2. 提取 contracts、pure preparation 与 shared persistence primitives；保持 façade compatibility aliases。
3. 提取 dependency、review 与 repair domains。
4. 提取 render lifecycle/support，运行 render/HyperFrames regression suite。
5. 提取 voice intent/candidate/activation，运行 ElevenLabs、voice/captions与 recovery suite。
6. 最后提取 recovery 与 core transaction；这些区域具有最高 crash-safety风险。
7. 最小更新 `AGENTS.md` module-boundary wording：façade及其 private implementation modules共同构成唯一 committer owner，而不是增加第二 writer。
8. 全部行为验证通过后，显式更新 Architecture Gate baseline并审查 deterministic diff。

每一波先保持 tests green再进入下一波；若机械提取暴露隐含耦合，应优先保留 transaction cohesion，而不是临时增加 public abstraction。

## 8. Verification Contract

### 8.1 Structural tests

- `ProductionStateCommitter` public identity与 constructor不变；
- 原有 public/direct/private compatibility symbols可从原路径 import；
- private `_state_commit_*` graph不存在 cycle或反向 import façade；
- façade不再承载多个完整 domain lifecycle，并显著低于当前 architecture debt；
- Architecture Gate接受 historical debt reduction，并将拆分后的新尺寸作为 ratchet。

### 8.2 Focused behavior suites

至少运行：

```bash
pytest -q tests/test_production_state_commit.py tests/test_production_state_recovery.py
pytest -q tests/test_production_hyperframes.py tests/test_production_elevenlabs.py tests/test_production_voice_captions_e2e.py tests/test_production_project.py
pytest -q tests/test_production_dependency.py tests/test_production_selective_rebuild.py
pytest -q tests/test_production_review.py tests/test_production_repair.py tests/test_production_mcp_review.py tests/test_production_mcp_optimize.py tests/test_production_mcp_apply.py
```

测试文件名以 implementation 时的 live repository truth为准；不存在或已更名的 suite应替换为最近等价测试并记录。

### 8.3 Completion verification

- repository full `pytest`；
- existing Harness integration与 Architecture Gate；
- crash-worker scenarios与重点 monkeypatch seam tests；
- import graph / compile check；
- `git diff --check`、完整 `git diff` 与 `git status`；
- Architecture baseline update前后分别运行 gate，确认 baseline不是用于隐藏增长。

## 9. Documentation and Rollback

`AGENTS.md` 只做最小 durable boundary clarification，不写拆分过程手册。Public docs无需新增用户行为说明，因为 runtime contract不变。

拆分应形成独立 implementation commit。若任一 transaction/recovery invariant无法由测试与 crash evidence证明保持，回滚整个 implementation commit；不得通过放宽断言、扩大 allowlist或刷新 baseline接受不确定行为。

## 10. Known Limits

本设计降低模块规模与内部耦合，但不声称静态结构能证明 semantic cohesion。它也不改变 dynamic import、runtime plugin关系或现有 transaction复杂度。成功标准是 single-writer contract和行为保持不变，同时把职责边界变成可维护、可由 Architecture Gate继续 ratchet 的代码结构。
