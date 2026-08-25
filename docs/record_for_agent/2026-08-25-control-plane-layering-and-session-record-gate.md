# Control-Plane Layering And Session Record Gate

Date: 2026-08-25

## Purpose

本文记录两个 durable control-plane 决策：保持 repository `AGENTS.md` 为 thin
constitution，把低频、host-specific与可漂移操作细节下沉到 `.agent/context/`；并把
`record-ai-video-session` 从“等待hook提醒”明确为 substantial AI-VIDEO work 的
completion-time proactive gate。

本记录只描述Development Governance。它不修改Product Runtime、Provider、Manifest、
Registry、Dependency Graph、Timeline、renderer、activation、P6或Final Acceptance。

## Layering And Deduplication Decision

Repository `AGENTS.md` 只保留durable authority、routing、canonical ownership、product
invariants、hard safety/decision gates、verification/completion contract与最小anchors。

以下内容进入`.agent/context/`：

- low-frequency execution procedures；
- host-specific absolute paths、environment/version与model/node location；
- startup/shutdown、diagnostic recipes与可漂移troubleshooting；
- Skill preflight、Agent Memory failure handling、credential lookup与implementation pitfalls。

Current runtime truth、phase status与historical experiment evidence仍分别归runtime baseline、
roadmap与`docs/record_for_agent/`，不能因为不适合`AGENTS.md`就统一塞进context。Detailed
surface/module mapping与focused verification只归`docs/agent-primary-contract-matrix.md`；
changed-path routing与check catalog只归`.agent/harness/policy.yaml`。`AGENTS.md`和context
只保存summary/anchor，不复制第二份catalog。

`.agent/bug-memory/`只用于真实发生、可复现且值得防止重犯的regression/incident。普通环境
说明、启动方式、设计建议或未发生风险不得伪装成bug memory。

Repository commit `accf43761b2af98cdfbd0818abe2608cfa3a9cb0`完成该下沉：

- `AGENTS.md`从280行降到218行；
- detailed Creative Skill、Agent Memory、credential与pitfall detail进入
  `.agent/context/control-plane-playbook.md`；
- duplicated module catalog从`AGENTS.md`与playbook移除，只保留contract-matrix owner。

Exact-range Harness receipt：

```text
.agent/harness/runs/20260825T024659913430Z/receipt.json
```

`184` tests、Documentation Contract与policy audit均通过；receipt freshness、snapshot、
scope、policy与artifact integrity均为true。

## Why Session Recording Was Missed

T8→LatentSync嘴型实验主要写入repository外的ComfyUI output与`/tmp`，没有立即产生可被
project hook归属的`apply_patch`或exact`git add`。因此hook没有注入
`capture_request_id`。这只能解释automatic backstop没有触发，不能免除Agent主动执行
`record-ai-video-session`：该Skill原本已要求substantial media work在stable checkpoint
后proactively record。

实际遗漏发生在completion routing：task从Shot Continuity replication连续转向speaking、
subtitle、T8-only graph、LatentSync与SyncNet，Agent在最终媒体交付前没有重新评估session
record gate。补写的媒体record为：

```text
docs/record_for_agent/2026-08-25-t8-latentsync-speaking-subtitle-experiment.md
```

Commit `ebb6bde7b1094028ae0c95f6a76c20636217b00d`；docs-only receipt：

```text
.agent/harness/runs/20260825T025033438328Z/receipt.json
```

## Proactive Completion Gate

Global `/home/reggie/.codex/AGENTS.md` 与repository `AGENTS.md` 现在都要求：当repository
提供dedicated session-record/capture Skill时，substantial implementation、documentation、
live proof、media diagnosis、architecture decision或recovery达到stable checkpoint、
completion、genuine blocker、handoff或compaction boundary后，必须在final response前评估。

Repository外authorized media/artifact effects同样计入。没有tracked diff、hook request或
`capture_request_id`不能解释为“不需要记录”。Unfinished work、trivial conversation和无
durable value的status check应明确判定为`no_record`，不得制造空泛记录。

`.agent/context/control-plane-playbook.md`的`Durable Session Record Gate`保存具体五步判断：

1. 判断work是否substantial且具备durable value；
2. 确认stable checkpoint/completion/genuine blocker；
3. 检查repository内外effects；
4. 条件成立时主动读取并执行Skill；
5. trivial/unfinished work明确`no_record`，record本身不得递归触发新record。

Repository commit `e0afea9b238e11c522d504bbe43602c2a11c3cbf`完成该gate。Exact-range
Harness receipt：

```text
.agent/harness/runs/20260825T030417241673Z/receipt.json
```

`184` tests、Documentation Contract与policy audit均通过，receipt verification全部通过。

## Effects And Boundaries

Repository effects只包含`AGENTS.md`、`.agent/context/control-plane-playbook.md`与本record。
Global `/home/reggie/.codex/AGENTS.md`不是Git-backed file；本轮只增加generic layering与
completion rules，不写project credential、runtime status或实验详情。

本次control-plane work没有运行media generation、没有Provider submit、没有paid effect、
没有修改Production code/state，也没有push或release。Unrelated `.codex/config.toml`与
`artifacts/`保持未修改、未stage、未commit。

## Agent Guardrails

- Hook是session-record backstop，不是唯一trigger owner。
- Repository外media effects不等于没有durable session work。
- `no_record`只适用于trivial、unfinished或无durable value的工作。
- Record只保存verified evidence与boundaries，不能授权新generation、Provider call、push、
  release或Production mutation。
- Control-plane record不替代`AGENTS.md`、playbook、contract matrix、Harness policy或tests。
