# AI-VIDEO Module Architecture Contract P0 Implementation Plan

## Status

Implemented in the authorized Architecture Gate P0 scope。Schema v2、direct-import dependency
rules、focused tests与canonical governance docs已按本计划落地；exact receipt、commit与publication
state由本轮最终交付单独报告，本文档本身不作为proof。该授权不包含修改Production Runtime、调用
Provider、生成媒体、刷新architecture baseline、push或release。

本计划基于 `main@d590494ba5424417e6b3aec3fe12127b8d4e523c` 的 tracked
Architecture Gate、Harness、contract matrix 与相关 tests 编写。当前共享 checkout 中已有的
Production Runtime、Harness policy、canonical docs 与其他 dirty/untracked changes 不属于本计划
证据，也不得由后续 executor 覆盖、stage 或 commit。

**Goal:** 在保留现有 Harness 和 Architecture Gate ownership 的前提下，为
`scripts.architecture_gate` 增加 baseline-independent、机器可执行的 Python module dependency
contract，使明确的禁止依赖能够在 exact task diff 上 deterministic fail closed。

**Scope:** 扩展 `architecture_gate.toml`、Architecture Gate policy model、import edge collection、
dependency rule evaluation、CLI findings、synthetic tests 与对应 canonical governance docs；声明四条
当前高置信度 macro-boundary rules。

**Contract Surfaces:** `architecture_gate.toml` schema、`python -m scripts.architecture_gate check`、
`update-baseline` 语义、Architecture finding JSON/text output、Harness 的
`task_architecture_gate` check 与 documentation contract。

**Invariants:** Harness 继续唯一拥有 exact diff、check routing、isolated execution 与 receipt proof；
Architecture Gate 继续唯一解释机器架构规则；`AGENTS.md` 与 contract matrix 继续拥有语义 authority；
Product Runtime 不得 import Development Governance；historical baseline 不得豁免 absolute dependency
contract；Gate 不得宣称证明 lifecycle、single writer、runtime call graph 或 media quality。

**Current / Target Behavior:** 当前 Gate 只阻止新增 oversized growth、new cycles，并报告 fan-out；
普通错误方向依赖会 PASS，function-local import 与 syntax failure 也不能形成可靠 contract evidence。
目标行为是在保留现有 LOC/fan-out/cycle ratchet 的同时，对 direct Python imports 建立独立、绝对的
module dependency findings。

**Compatibility:** Repository config 升级到 `schema_version = 2`；loader 继续接受 schema v1，
并将其解释为“没有 dependency contract”，保持历史 fixture/repository 的现有 Gate 行为。
现有 finding IDs、exit semantics、baseline path 与 Harness argv 不变。新增 rule IDs 使用
`ARCH100+`，不得复用 `ARCH001`–`ARCH005`。

**Out of Scope:** 独立 `architecture-manifest.yaml`、`modular-sdd` Skill、Production Runtime
大规模拆分、public API registry、symbol-level call enforcement、dynamic import analysis、Node/workflow
dependency、lifecycle/activation/timeline correctness、remote ruleset 配置、Provider/media execution。

**Acceptance Criteria:** 四条 P0 rules 对当前 committed source 无 violation；synthetic tests 证明
top-level/function-local/relative imports、`TYPE_CHECKING`、syntax failure、exact exception 与 baseline
隔离语义；existing Gate tests 保持通过；exact staged snapshot 获得 fresh passing Harness receipt。

**Verification:** focused Architecture Gate tests、docs contract check、Harness policy audit、task-delta
Gate、exact staged Harness verification 与 receipt freshness verification。

**Spec / ADR:** 无独立 spec。Authority 来自 `AGENTS.md`；semantic owner 与 invariant anchors 来自
`docs/agent-primary-contract-matrix.md`；本 plan 只约束一个 Development Governance implementation
slice。

## Decision Summary

P0 采用以下固定决策：

```text
VERDICT: PARTIALLY
Harness: KEEP
Architecture Gate: EXTEND
Module Architecture Contract: ADD
modular-sdd Skill: DO NOT ADD
```

`Module Architecture Contract: ADD` 只表示在现有 `architecture_gate.toml` 中加入静态依赖规则；
不得创建覆盖所有 module owner、public API、runtime lifecycle 或 canonical contract 的全量 manifest。

## Problem Boundary

### Current Enforcement

当前 `architecture_gate.toml` 只声明 `source_roots`、baseline、LOC、fan-out、exclude 与 size
exceptions。`build_snapshot()` 虽然临时构建 import graph，但 snapshot 只保留 per-file metrics 和
cycles；精确 edges 不进入 policy evaluation。

`_module_imports()` 只遍历 module-level `tree.body`，因此 function-local imports 不参与 cycle；
`SyntaxError` 被解释为空 imports。`_compare()` 只处理 oversized growth、new oversized module、new
cycle、fan-out threshold crossing 与 baseline freshness。现有 test 也明确允许不构成 cycle 的普通新依赖。

Harness 已经拥有并应继续拥有：

- exact staged/range scope discovery；
- changed path 到 mandatory checks 的 policy routing；
- detached temporary worktree execution；
- exact policy、snapshot、artifact hash、check output 与 receipt freshness proof。

因此缺口属于 Architecture Gate rule vocabulary，不属于 Harness orchestration。

### Current Boundary Evidence

P0 需要覆盖的高置信度规则已经散落在 contract tests 和 human contracts 中：

- Product Runtime 不得依赖 `scripts.*` Development Governance；
- Legacy `cli.py`、`manifest.py`、`pipeline.py` 不得反向依赖 `ai_video.production`；
- `src/ai_video/production/**` 不得反向依赖 `ai_video.planning`、
  `ai_video.quality_gates` 或 `ai_video.quality_intelligence`；
- 任意 `src/ai_video/production/_state_commit_*.py` 不得 import
  `ai_video.production.state_commit` façade。

当前源码还存在不适合作为 P0 hard rule 的 seams：

- `_image_project_reader` 与 `_video_project_reader` 使用 function-local imports 形成双向 reader
  dependency；
- `video_generation.py` 消费 committer private members；
- Production Comfy adapters 复用 Legacy private `_set_path`；
- `production/__init__.py` 是高 fan-out public façade；
- `production/models.py` 聚合多个 domain contracts。

这些 seams 证明完整 public/internal 或 ownership enforcement 需要先迁移源码；P0 不得用 broad
exceptions 把它们伪装成已解决，也不得顺带重构这些 Runtime files。

### Baseline Separation

`.architecture/architecture-baseline.json` 是 historical LOC/cycle/fan-out debt ratchet，不是 desired
module inventory。Dependency rules 必须每次绝对求值：

- `update-baseline` 不得写入、接受或清除 dependency violations；
- 新增 rule 不得因当前违规而自动 grandfather；
- 若某条 proposed rule 在 committed source 上已有 violation，必须先缩小/修正 rule 或另立明确
  migration slice，不能刷新 baseline 或添加 wildcard exception。

## Target Architecture

```text
task-local SDD / spec / plan
        non-authoritative design input
                       │
                       ▼
AGENTS.md ──────── docs/agent-primary-contract-matrix.md
authority           semantic owners / invariants
                       │ contract_ref only
                       ▼
architecture_gate.toml
machine projection: module sets + dependency rules + exact exceptions
                       │
                       ▼
scripts.architecture_gate
parse imports → evaluate absolute rules → stable findings
                       │
                       ▼
existing Harness
exact diff → routed checks → detached proof → receipt
```

## Source-of-Truth Contract

| Concern | Single Owner | Forbidden Duplication |
| --- | --- | --- |
| durable authority、product invariants、decision gates | `AGENTS.md` | 不保存完整 module catalog |
| human-readable semantic owner、forbidden alternate path、verification anchor | `docs/agent-primary-contract-matrix.md` | 不复制 TOML rule tables |
| statically enforceable module sets、dependency rules、exact exceptions | `architecture_gate.toml` | 不描述 runtime lifecycle 或 current phase status |
| parsing、evaluation、diagnostics | `scripts/architecture_gate/**` | Python source 不 hard-code repository rule list |
| changed path → checks、isolated execution、proof | `.agent/harness/policy.yaml`、Harness runner | 不保存 module dependency direction |
| implementation proposal | task-local spec / plan | 不成为 accepted runtime or architecture truth |
| Codex guidance | `AGENTS.md` + Gate output | 不新增 `modular-sdd` rule copy |

若后续需要更好的 Codex discoverability，应另行评估只读
`architecture_gate explain <path-or-module>`；它只能读取同一 TOML policy。P0 不增加该 command，
也不增加 Skill。

## File Ownership and Change Map

| Path | P0 Responsibility | Old-Path Decision |
| --- | --- | --- |
| `architecture_gate.toml` | 升级 schema，声明 module sets、四条 dependency rules | 保留现有 thresholds、baseline 与 size exceptions |
| `scripts/architecture_gate/models.py` | 增加 policy、edge、rule、exception types | 保留 existing `Policy`/`FileMetric`/snapshot fields 与 finding semantics |
| `scripts/architecture_gate/metrics.py` | 收集 normalized direct import edges，并区分 runtime/type-checking | 保留 LOC、fan-out、SCC cycle algorithm；不分析 dynamic imports |
| `scripts/architecture_gate/gate.py` | 加载/验证 schema v2，求值 absolute dependency rules | `update-baseline` 继续只写 metrics/cycles baseline |
| `scripts/architecture_gate/__main__.py` | 仅在现有 output wiring 需要时适配新 findings | 不新增第二 CLI entrypoint 或 `explain` command |
| `tests/test_architecture_gate.py` | synthetic rule/parser/baseline-isolation tests | 保留 current regression tests |
| `tests/test_architecture_gate_cli.py` | CLI exit/output compatibility tests | 保留 single repository entrypoint |
| `docs/agent-primary-contract-matrix.md` | 增加 machine projection 与 blind-spot boundary | 不复制四条 TOML rule bodies |
| `docs/v0.2-runtime-baseline.md` | 实现后记录 Architecture Gate current capability | 不把 plan 描述成 implemented truth |

P0 不修改 `.agent/harness/policy.yaml`、`scripts/agent_harness*.py`、`AGENTS.md`、
`.architecture/architecture-baseline.json` 或任何 `src/ai_video/**`。现有 policy 已把 Gate config、source
和 tests 路由到 `architecture_tests` 与 `task_architecture_gate`。

## Machine Contract

### Module Sets

Schema v2 使用 named `module_sets` 作为 reusable match sets。它们不是 semantic ownership，也不要求
覆盖所有 Python files；一个 path 可以属于多个 sets，从而同时受 cross-cutting 与 subsystem rules
约束。P0 sets 至少包括：

- `ai_video_product_source`: `src/ai_video/**/*.py`；
- `legacy_core`: `src/ai_video/cli.py`、`manifest.py`、`pipeline.py`；
- `production_runtime`: `src/ai_video/production/**/*.py`；
- `state_commit_private_modules`: `src/ai_video/production/_state_commit_*.py`。

这种语义避免把 Harness categories 或 directory names 错当成唯一 module ownership。真正的 module
ownership declaration 必须等现有 public/private seams 收敛后另行决策。

### Import Edge

每条 direct import edge 至少包含：

- `source_path`；
- normalized `source_module`；
- normalized absolute `target_module`；
- `lineno`；
- `context = runtime | type_checking`；
- relative import 是否已经结合 source package 正确解析。

Parser 必须遍历 top-level 与 function/class/control-flow 内的 direct `import` / `from` nodes。
`if TYPE_CHECKING:` 内 imports 要被识别但默认不触发 runtime dependency rule。`importlib`、字符串模块名、
plugin discovery 与 runtime registry 不在 P0。

Contract referenced target prefixes 即使不位于 `source_roots` 也必须保留，例如 `scripts.*`；其他第三方
imports 不参与 first-party dependency rule。受管 source 出现 `SyntaxError` 时产生 hard `ARCH100`，
不得返回空 dependency set。

### Dependency Rules

每条 rule 必须声明：

- stable `id`；
- source `module_set`；
- exact forbidden target module 或 target prefix；
- `contract_ref`，指向 contract matrix 的 owner/invariant anchor；
- `severity = error`。

P0 rule set：

| Rule ID | Source | Forbidden Target | Purpose |
| --- | --- | --- | --- |
| `ARCH101` | `ai_video_product_source` | `scripts` prefix | Product Runtime 与 Development Governance 隔离 |
| `ARCH102` | `legacy_core` | `ai_video.production` prefix | 保持 Legacy/Production 单向边界 |
| `ARCH103` | `production_runtime` | `ai_video.planning`、`ai_video.quality_gates`、`ai_video.quality_intelligence` prefixes | 防止 Production reverse ownership |
| `ARCH104` | `state_commit_private_modules` | exact `ai_video.production.state_commit` | 防止 private committer modules 反向依赖 façade |

Diagnostics 必须稳定输出 rule id、source path/line、normalized target 与 `contract_ref`。同一 edge 命中
同一 rule 多次时只输出一个 finding；不同 rules 的独立 violations 不合并。

### Exact Exceptions

Schema 支持 exception，但 P0 repository config 不预置 exception。Exception 必须绑定：

- exact `rule_id`；
- exact `source_path`；
- exact normalized `target_module`；
- `owner_ref`；
- `reason`；
- `review_by` 日期。

禁止 source/target wildcard exception。Unknown rule、missing source、重复 exception、过期
`review_by` 或 exception 不再匹配实际 edge时必须产生 configuration error 或 stale-exception error；
不得静默接受。Exception 不进入 architecture baseline。

## Major Milestones

### Milestone 1: Establish Schema v2 Without Changing Existing Gate Semantics

**Files:**

- Modify: `architecture_gate.toml`
- Modify: `scripts/architecture_gate/models.py`
- Modify: `scripts/architecture_gate/gate.py`
- Test: `tests/test_architecture_gate.py`

**Contract:** Loader 接受 schema v1 与 v2。v1 完全保持 current metrics-only behavior；v2 对
`module_sets`、dependency rules 和 exceptions 做 strict typed validation。Repository config 升级为 v2，
但本 milestone 尚不启用 rules。

**Implementation Notes:** Config validation 必须拒绝 unknown module set、duplicate rule id、empty target、
unsupported severity、wildcard exception 与 invalid `review_by`。新增 policy types 保持 immutable；
repository-specific rule values只能来自 TOML，不能写死在 Gate Python source。

**Acceptance:** Existing v1 fixture tests 不改语义；v2 valid/invalid fixtures deterministic PASS/FAIL；现有
LOC/fan-out/cycle findings 与 baseline loading结果不变。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_architecture_gate.py -q
```

### Milestone 2: Preserve Direct Import Edges and Fail Closed

**Files:**

- Modify: `scripts/architecture_gate/models.py`
- Modify: `scripts/architecture_gate/metrics.py`
- Test: `tests/test_architecture_gate.py`

**Contract:** `build_snapshot()` 在不改变 existing per-file fan-out 与 SCC cycle behavior 的前提下，
提供 normalized direct import edges 给 dependency evaluator。Function-local imports进入 dependency
rules；`TYPE_CHECKING` imports被标记但默认不进入 runtime rules；syntax failure产生 hard evidence gap。

**Implementation Notes:** Relative import 必须基于 source module/package 解析，不能只拼接字符串。
Contract referenced non-source prefix必须保留；普通 third-party imports继续排除，避免把 dependency
installation policy混入 Architecture Gate。不得执行 imported code。

**Acceptance:** Synthetic fixtures 证明 top-level、function-local、nested-control-flow 和 relative import
形成准确 edge；`TYPE_CHECKING` 不产生 runtime violation；syntax error 返回 `ARCH100`；现有 cycle tests
保持兼容。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_architecture_gate.py -q
```

### Milestone 3: Enforce Baseline-Independent Dependency Rules

**Files:**

- Modify: `scripts/architecture_gate/gate.py`
- Modify: `scripts/architecture_gate/__main__.py` only if current output plumbing requires it
- Test: `tests/test_architecture_gate.py`
- Test: `tests/test_architecture_gate_cli.py`

**Contract:** Dependency rules对 current snapshot 绝对求值，不与 base/baseline snapshot做 delta comparison。
`check --base-ref` 仍使用 base ref 计算 existing metrics regressions，但不得把 base 中已存在的 forbidden
edge视为可接受。`update-baseline` 即使成功也不能清除 dependency finding。

**Implementation Notes:** Findings 使用 `ARCH101`–`ARCH104`；configuration/stale exception errors 必须
返回 non-zero。JSON/text output 延续当前 deterministic ordering。Exact exception只豁免一条 exact edge，
且仍在 diagnostics 中以 auditable non-error metadata 表示或由 dedicated config validation覆盖。

**Acceptance:** allowed edge PASS；每类 forbidden edge ERROR；exact exception仅豁免匹配 edge；过期和
stale exception FAIL；运行 `update-baseline` 后同一 forbidden edge仍 FAIL；CLI exit status 与 JSON
finding稳定。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q
```

### Milestone 4: Activate the Four Repository Rules

**Files:**

- Modify: `architecture_gate.toml`
- Test: `tests/test_architecture_gate.py`

**Contract:** 只启用 `ARCH101`–`ARCH104`。每条 rule 必须引用 contract matrix anchor；不得增加
public/internal、reader cycle、committer private consumer 或 Legacy private helper rules。

**Implementation Notes:** 激活前在 committed `HEAD` 上运行 rule audit；若发现 violation，停止该 rule
的 activation并报告具体 edge。不得用 baseline refresh、broad glob exception 或 Runtime refactor在同一
P0 中强行达成 PASS。Repository config 初始不保存 exception。

**Acceptance:** Current committed tree 对四条 rules为 PASS；为每条 rule增加 synthetic violating fixture，
证明它实际阻断对应 dependency；同名 module、relative import 与 function-local形式不能绕过。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m scripts.architecture_gate check --base-ref HEAD --format json
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q
```

### Milestone 5: Record the Implemented Governance Boundary

**Files:**

- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`

**Contract:** Contract matrix只说明 Architecture Gate 能强制 direct Python dependency rules、配置的
canonical machine owner及其 blind spots，并指向 `architecture_gate.toml`；runtime baseline只在 code
与 tests 实际完成后记录 current implemented capability。

**Implementation Notes:** 不在 docs 复制四条完整 rule table，不把 static PASS描述为 module ownership、
canonical writer、runtime call graph、SDD compliance、remote protection或 Production acceptance。
`AGENTS.md` 已有 Development Governance 与 Architecture Gate routing，不在 P0 重写。

**Acceptance:** Docs contract gate通过；docs不存在第二份 machine rule registry；planned/implemented状态与
code/tests一致。

**Verification:**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m scripts.docs_contract_gate check
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider \
  tests/test_docs_contract_gate.py tests/test_agent_harness.py -q
```

### Milestone 6: Produce Exact Harness Proof

**Files:**

- No product or Harness source changes
- Stage only the exact P0-owned files listed above

**Contract:** Completion proof必须来自 non-empty exact staged snapshot或 exact commit range；unrelated
dirty changes不得进入 stage、detached execution tree或 receipt scope。Harness本身不增加 SDD或
architecture semantics。

**Implementation Notes:** 先检查 live writers和same-file ownership；使用
`git add <specific-files>`。若任一 target file已有他人未提交改动，必须在写入前按 repository rule停止并
由用户决定 ownership/sequence。不得 stage `.architecture/architecture-baseline.json`。

**Acceptance:** Harness inspect只选择预期 documentation/architecture checks；fresh verification PASS；
receipt的 changed paths、policy hash、snapshot hash与 staged files一致；receipt freshness verification
PASS。Repository full baseline Gate若因 pre-existing stale debt失败，必须单独如实报告，不能用 task receipt
掩盖，也不能在本 slice刷新 baseline。

**Verification:**

```bash
git diff --check -- \
  architecture_gate.toml \
  scripts/architecture_gate/models.py \
  scripts/architecture_gate/metrics.py \
  scripts/architecture_gate/gate.py \
  scripts/architecture_gate/__main__.py \
  tests/test_architecture_gate.py \
  tests/test_architecture_gate_cli.py \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md

PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness inspect --staged
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness verify --staged
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness verify-receipt \
  --receipt <repository-relative-receipt-path>
```

`<repository-relative-receipt-path>` 不是待填写的设计决策；它由该次 Harness verify 输出生成，executor
必须使用实际输出路径，不得预设或复用历史 receipt。

## Old-Path Retirement

P0 不删除 current Gate、Harness 或 Production Runtime path。只进行以下收敛：

- Architecture dependency rule interpretation只存在于 `scripts.architecture_gate`；
- 新增 architecture tests只测试 engine semantics与 synthetic repository behavior；
- 现有 hard-coded structure tests在 P0 保留，因为其中还包含 LOC、MRO 或 behavior assertions；
- 后续只有在 Gate rule与原 test assertion完全等价并已有 fresh proof时，才可单独删除重复的纯 import
  assertion。不得在本 P0 顺带清理。

## Rollback

若 P0 implementation需要 rollback：

1. 将 repository `architecture_gate.toml` 恢复为 schema v1并移除 module sets/rules；
2. 移除新增 dependency evaluator与对应 tests，同时保留原有 LOC/fan-out/cycle Gate；
3. 恢复 contract matrix/runtime baseline中的 implemented claim；
4. 不修改 architecture baseline，不触碰 Product Runtime，不改变 Harness receipt semantics。

Rollback必须针对 P0-owned files进行普通 revert，不得使用 broad reset、clean或覆盖共享 checkout。

## Principal Risks

- **Second source of truth:** TOML复制 semantic owner或 runtime lifecycle，会与 `AGENTS.md`/matrix漂移。
- **False proof:** static import PASS不能证明 mutation、activation、timeline、replay或canonical writer正确。
- **Parser blind spots:** dynamic imports、re-export、Node/workflow和runtime dataflow仍不受约束。
- **Exception laundering:** wildcard、过期或不再命中的 exception会把架构债务永久合法化。
- **Baseline laundering:** 通过 `update-baseline`接受 forbidden edge会破坏 absolute contract。
- **Premature public/internal enforcement:** 当前 private reader/committer/helper seams未收敛，立即 hard gate
  会产生大量例外并冻结错误结构。
- **Rule-and-code same change:** contributor可同时修改 TOML 与 source；hard enforcement还依赖 code review和
  live required checks，workflow文件本身不证明 remote branch protection。
- **Dirty shared checkout:** concurrent writer若修改同一 target file，会使 diff、tests与receipt ownership不可信。
- **Stale repository baseline:** full Gate当前 historical baseline可能与 current tree不一致；P0 task-delta PASS
  不能被描述为 repository architecture debt已经清零。

## Completion Boundary

P0完成只证明：accepted TOML rules能对 direct Python import edges deterministic hard fail，并由现有
Harness对 exact change生成proof。它不证明 SDD adoption、完整 module ownership、public/internal API、
Production Runtime重构、remote enforcement、Provider/media quality、P6或Final Acceptance。
