# Local ComfyUI Authorization Exemption Record

Date: 2026-08-28

## Purpose

本文记录 AI-VIDEO development governance 对本地 ComfyUI 的 durable authorization policy：严格
loopback、完全 local/unmetered 且无 cloud egress 的 ComfyUI actions 不再要求 user authorization、
task-scoped authorization 或额外 confirmation。

这是 Agent execution policy，不是 Product Runtime capability、Provider selection、media acceptance、
Production activation、P6、Final Acceptance、publication 或 release truth。用户 task scope、当前 code、
tests、sealed contracts 与真实 runtime evidence 仍决定某个具体 action 是否可执行。

## Durable Decision

Authorization exemption 覆盖与 accepted task 直接相关的：

- local ComfyUI `status` / `start` / `stop` lifecycle；
- image 与 video generation；
- bounded retry、variant 与 benchmark。

用户不需要先点名 local ComfyUI，也不需要为 exact preview 再提供 approval。既有 seam 若要求 exact
preview，它继续作为 readiness / provenance evidence，而不是 user-approval gate。

该 exemption 仅在 endpoint 严格 loopback、execution 完全 local/unmetered 且没有 cloud egress 时成立。
任何非 loopback、effect identity 无法证明、可能 cloud egress、metered、remote 或 paid action 都回到
对应 Provider authorization、budget、egress、secret、intent 与 permit gates。

## Unchanged Safety And Ownership

移除 user-approval layer 不改变以下 contracts：

- 用户明确的 read-only、禁止 live generation / media effects 或更高优先级限制仍立即停止 action；
- action 必须与 accepted task 直接相关，exemption 不授权 unrelated media work 或 scope expansion；
- exact request / tool / provider / profile / workflow / binding / input / output identity 与 content-addressed
  provenance 继续 fail closed；
- AI-VIDEO local video generation 继续通过 `VideoGenerationService`、durable local intent、committer-issued
  one-use permit 与唯一 `ProductionStateCommitter`；不得直接调用 Comfy transport 或 Provider `submit()`；
- Agent-side local image authoring继续使用既有 tool/provider seam、input/output provenance 与 image-level Gate；
- unknown outcome 继续 fail closed；不得 blind retry、fallback、permit remint 或重复 side effect；
- retry、variant 与 benchmark 必须是 bounded、task-relevant 且具有新 exact identity 的 attempt；
- Per-Shot `FAIL` / `NOT_EVALUATED` 继续停止当前 batch。后续 local repair attempt 无需用户授权，但必须
  独立重新进入全部 Provider 与 media gates，不能自动串联；
- technical PASS、tool success 或 exemption 本身不产生 HUMAN PASS、Production qualification、P6、
  Final Acceptance、activation、push、release 或 publication truth。

## Canonical Surfaces Updated

- `AGENTS.md`：新增 durable `Local ComfyUI Authorization Exemption`，并从 generic live-smoke / benchmark
  Decision Gate 中排除符合条件的 local ComfyUI actions。
- `.agent/context/control-plane-playbook.md`：拥有 detailed applicability、canonical execution seam、retry、
  variant、benchmark、unknown-outcome 与 Per-Shot stop behavior。
- `docs/agent-primary-contract-matrix.md`：同步 Local-First Provider Safety、Local ComfyUI Supervisor 与
  `Submit Local Video` surface。
- `docs/v0.2-runtime-baseline.md` 与 `docs/v0.2-agentic-production-roadmap.md`：只校正 current-facing local
  ComfyUI authorization status；historical calls、M8/H3 evidence、quality state 与 deferred milestones 不变。

## Verification And Evidence

Focused documentation/control-plane verification：

```text
python -m pytest -p no:cacheprovider \
  tests/test_comfyui_supervisor.py \
  tests/test_agent_harness.py \
  tests/test_runtime_skill_boundary.py -q
152 passed

python -m scripts.docs_contract_gate check
Documentation contract gate passed.
```

Exact Harness checkpoint 使用：

```text
.agent/harness/runs/local-comfyui-auth-exemption-20260828/receipt.json
```

本次 policy work 没有启动/停止 ComfyUI，没有生成或编辑图片/视频，没有调用 Provider、
`video-analysis`、remote/paid API 或 secret。它只改变未来 Agent actions 的 authorization boundary；
没有声称 local runtime 或 media quality 因文档更新而改变。

## Publication And Remaining Boundary

本记录 checkpoint 只提交到当前 local `main`；没有 push、release 或 remote publication。
`.codex/config.toml`、`artifacts/` 与既有 unrelated untracked plan/spec/record 均不属于本 task，必须保持
未 stage、未 commit、未覆盖。

未来具体 local ComfyUI attempt 仍须证明 exemption prerequisites 与 applicable technical gates；若 endpoint、
metering 或 egress identity 不清楚，应按不满足 exemption 处理，而不是猜测为 local。
