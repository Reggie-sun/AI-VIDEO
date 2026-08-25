# Per-Shot Post-Media Gate Record

Date: 2026-08-25

## Purpose

本文记录一次 multi-Shot generation control-plane 修正：前置 readiness / Provider gates
已经阻止不合格 request，但 Agent-controlled batch 曾在每个 MP4 落盘后直接继续提交下一
Shot，只把 Generated-Video Analysis Hook 当作后台 advisory work，导致真正的 post-media
stop condition 缺失。

本记录描述的是 Agent execution contract，不证明 Product Runtime Gate 2、P6 review、
automatic semantic evaluator 或 Final Acceptance 已实现。

## Current Contract

当 Agent 控制 sequential multi-Shot generation 时，流程固定为：

```text
generate Shot N once
  -> bind exact MP4 path and SHA-256
  -> explicitly call project-local video-analysis MCP
  -> map raw evidence to exact Shot requirements
  -> PASS: allow Shot N+1 submit
  -> FAIL / NOT_EVALUATED: stop before any next submit
```

Gate 必须产生 requirement-level findings；不得用一个总分覆盖 identity、action、
product/object、camera、duration、prompt adherence、audio 与 continuity。MCP unavailable、
evidence missing/stale、output identity drift 或 required requirement 无法可靠判定都属于
`NOT_EVALUATED`，并 fail closed。

异步 Generated-Video Analysis Hook、command exit code、MP4 文件存在、OpenVideo judge score
与 env-unset auto-PASS stub 均不能满足该 Gate。当前 `LongFilmPipeline.make_film()` 没有等待
external MCP 的 synchronous stop point，因此不能作为 AI-VIDEO unattended multi-Shot
generation path；Agent 必须逐 Shot 生成、Gate，再 stitch accepted media。

## Ownership Boundary

- `AGENTS.md` 保存不可绕过的 durable invariant。
- `.agent/context/control-plane-playbook.md` 独占详细顺序、input/output evidence 与 stop
  semantics。
- `.agents/skills/h3-video/SKILL.md` 与 `.agents/skills/open-video/SKILL.md` 将该 contract
  落入实际 generation procedure。
- Project-local `video-analysis` MCP 只提供绑定 exact bytes 的 raw evidence。
- Agent-side verdict 不得写 Manifest、Registry、candidate activation、P6 receipt 或 Final
  Acceptance；进入 Production acceptance 仍由 existing review contract 与
  `ProductionStateCommitter` 重新绑定、adjudicate 和持久化。

因此，本次修正不改变 `ProductionStateCommitter`、`ResolvedTimeline`、Provider lifecycle、
P6 或 Final Acceptance ownership，也不把 Development Gate PASS 描述成 Production PASS。

## Verification And Evidence

Control-plane commit：`bc00db07b160eb545d33415c5f2391234bbe1323`（`docs: require
per-shot post-media gate`）。

Changed paths：

- `AGENTS.md`
- `.agent/context/control-plane-playbook.md`
- `.agents/skills/h3-video/SKILL.md`
- `.agents/skills/open-video/SKILL.md`

Focused verification：

- `python -m scripts.docs_contract_gate check`：passed。
- Harness/control-plane tests：`185 passed`。
- ComfyUI supervisor tests：`16 passed`。
- Exact commit-range Harness receipt：
  `.agent/harness/runs/20260825T122144315027Z/receipt.json`。
- `make harness-receipt`：`passed=true`、`fresh=true`、`fresh_for_snapshot=true`、
  `scope_paths_match=true`、`artifact_integrity=true`、`closure_eligible=true`。

本次变更没有执行 Provider submit、媒体生成、paid/cloud call、P6 adjudication 或 human
quality acceptance。共享 checkout 中其他 staged/dirty files 与 `artifacts/` 未被本次 commit
包含或修改。

## Remaining Boundary

当前仓库没有拥有 multi-Shot Provider submission 的 canonical Product Runtime batch
orchestrator。因此本次只修复 Agent-controlled execution；若未来新增正式 batch API，必须在
该唯一 orchestrator 中复用同一 fail-closed barrier，并通过 existing P6/committer lifecycle
持久化 Production evidence。不得仅靠 skill prose 推断未来 Runtime 已获得该能力。

## Agent Guardrails

- 不要先生成完整 batch 再补分析。
- 不要等待用户提醒才调用 `video-analysis` MCP。
- 不要把 background hook result、auto-PASS、file existence 或单一 score 当作 Gate PASS。
- `FAIL` / `NOT_EVALUATED` 后先停止并报告 targeted diagnosis；不得 silent retry、fallback
  或继续下一 Shot。
- Agent-side Gate 与 Production P6 / Final Acceptance 始终是不同 proof layers。
