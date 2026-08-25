# Module Architecture Contract P0

## Purpose

本记录固化 2026-08-25 完成的 Architecture Gate P0：在保留现有 Harness 的前提下，为现有 Gate 增加 machine-readable module dependency contract，并由确定性静态检查强制执行。它不建立第二套 Harness、独立 architecture manifest 或 `modular-sdd` Skill，也不改变 Production Runtime。

对应 implementation plan：`docs/superpowers/plans/2026-08-25-ai-video-module-architecture-contract-p0.md`。

## Current Development Governance Truth

- `AGENTS.md` 继续拥有 durable authority、canonical ownership 与 product invariants。
- `docs/agent-primary-contract-matrix.md` 继续是 detailed human-readable surface owner、forbidden alternate path 与 focused verification 的唯一 owner。
- `architecture_gate.toml` 只拥有可执行的 Architecture Gate 配置；schema v2 在同一文件中声明 module sets、dependency rules 与 dated exceptions。
- `scripts/architecture_gate/` 解释并执行该 machine-readable contract。
- `.agent/harness/policy.yaml` 与 `scripts/agent_harness.py` 继续拥有 changed-path routing、mandatory checks 与 exact proof；Harness 没有被替换。
- Source code、tests 与 exact Harness receipt 仍是 executable evidence。Plan、record、Skill 或历史 receipt 不产生 runtime truth。

因此，本 P0 没有添加独立的 architecture manifest。`architecture_gate.toml` 就是 Gate 的单一 machine-readable input；human intent 只在 canonical owner 中保留不重复的解释与 pointer。

## Implementation And Decisions

Local task commit：`ee106eaac0353a484f9b9de0354fc1ed622a2e29`，base commit：`8ac8c2e13d734857091d7c77e052b717ed71e21e`。

主要实现：

- `architecture_gate.toml` 升级到 schema v2，声明 `ai_video_product_source`、`legacy_core`、`production_runtime` 与 `state_commit_private_modules` module sets。
- 新增四条 active repository rules：
  - `ARCH101`：`src/ai_video/**` 禁止依赖 `scripts` prefix。
  - `ARCH102`：Legacy core 禁止依赖 `ai_video.production` prefix。
  - `ARCH103`：Production 禁止反向依赖 `ai_video.planning`、`ai_video.quality_gates` 与 `ai_video.quality_intelligence`。
  - `ARCH104`：`_state_commit_*.py` 禁止 exact dependency `ai_video.production.state_commit`，保护 canonical writer boundary。
- schema v1 保持 metrics-only compatibility；schema v2 对 unknown top-level fields、错误 schema type、非 table module sets、无匹配文件的 active module set 与无效 exception fail closed。
- Python AST dependency extraction 覆盖直接 `import`、`from ... import ...`、relative import、nested import，以及标准 `TYPE_CHECKING` / `typing.TYPE_CHECKING` 分类。
- Contract violations 是 absolute current-snapshot failures，不依赖 baseline，也不能由 `update-baseline` 储存或豁免。
- Exception 必须绑定 exact rule、module set 与 target，并包含 `owner`、`reason`、`review_by`；过期或格式无效时 fail closed。

本 P0 不分析 dynamic imports、`TYPE_CHECKING` aliases、JavaScript/Node dependency graph 或 runtime call graph。这些边界保持显式，避免把静态 import Gate 误称为完整 architecture proof。

## TDD And Independent Review

实现按 RED-GREEN 回归推进。最终 focused suite：

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_architecture_gate.py tests/test_architecture_gate_cli.py -q
58 passed in 1.18s
```

`reviewer_xhigh` 的初次独立复审拒绝了两个 semantic defects：schema v2 可被 unknown top-level table 或非整数 schema value 静默禁用，以及 external exact rule 可被 `from scripts.tool import value` 绕过。随后添加 RED regressions 并修复；同一 reviewer 的 scoped re-review verdict 为 `accept`。复审还推动 active-but-empty module set 变为 `ARCH100` fail-closed evidence。

Reviewer verdict 是独立 design/code evidence，不替代 tests、Architecture Gate 或 Harness receipt。

## Exact Harness Evidence

对 exact commit range `8ac8c2e13d734857091d7c77e052b717ed71e21e..ee106eaac0353a484f9b9de0354fc1ed622a2e29` 执行：

```text
PYTHONDONTWRITEBYTECODE=1 python -m scripts.agent_harness verify \
  --base-ref 8ac8c2e13d734857091d7c77e052b717ed71e21e \
  --head-ref ee106eaac0353a484f9b9de0354fc1ed622a2e29 \
  --run-id architecture-contract-p0-20260825-v1
```

Selected categories 为 `harness_control`、`documentation`、`architecture_tooling`、`control_plane`。结果：

- Documentation contract：passed。
- Policy audit：clean。
- task-delta Architecture Gate：PASS，`0` errors / `0` warnings / `0` info。
- Harness tests：`185 passed in 4.00s`。
- Architecture tests：`58 passed in 1.17s`。

Receipt：`.agent/harness/runs/architecture-contract-p0-20260825-v1/receipt.json`。`verify-receipt` 已确认 artifact integrity、check records、coverage closure、freshness、policy match、exact scope、snapshot match、workspace cleanup/stability 与 self-consistency 均为 true。

## Publication And Workspace State

- Implementation 只在 local `main` commit；本任务没有 push、release 或 remote protection claim。
- 本任务没有调用 Provider、ComfyUI、paid service 或生成媒体，也没有刷新 Architecture Gate baseline。
- `docs/agent-primary-contract-matrix.md` 与 `docs/v0.2-runtime-baseline.md` 的 endpoint-repair staged hunks 是用户明确选择保留并叠加的既有工作；同一 task commit 包含它们不表示 Architecture Gate P0 拥有相邻 endpoint implementation。
- 其他 unrelated staged、unstaged 与 untracked work 保持原样，未由本任务 reset、覆盖或提交。
- Project RAG 的 `all` scope 查询仅作为 advisory preflight；其中部分 current-doc/superpowers shards 陈旧并进入 detached refresh queue，因此没有被当作当前 runtime、policy 或 proof source。

## Remaining Boundaries

- P0 只强制 direct Python import dependency direction。若未来需要 public/internal export surface、canonical contract symbol ownership 或跨语言图，应先给出可执行的真实违规样本，再扩展同一个 Gate schema；不要建立并行 manifest owner。
- `modular-sdd` Skill 当前不添加。Codex guidance 继续由 thin `AGENTS.md` constitution、contract matrix、active plan/spec 与 Gate diagnostics 组合提供；只有出现可重复的 planning/coding failure 且无法由这些 owner 解决时才重新评估 Skill。
- Architecture Gate 证明声明的静态 dependency rules 在 exact snapshot 上成立；它不证明 production lifecycle、provider behavior、media quality、human acceptance、release 或 remote availability。

## Agent Guardrails

后续修改本能力时：

1. 保持 `architecture_gate.toml` 为唯一 machine-readable module-rule owner，不复制到第二 manifest。
2. 先添加能够复现真实绕过或 regression 的 test，再修改 parser/evaluator。
3. 新 rule 默认 absolute、fail closed；exception 必须 exact、dated、owned、reviewable。
4. 不用 baseline refresh 隐藏 current violation，也不让 Harness receipt替代 Gate semantics。
5. 任何 Production Runtime、schema、writer/lifecycle owner 或 Provider scope 变化仍按各自 canonical contract 和 decision gate 单独批准、实现与验证。
