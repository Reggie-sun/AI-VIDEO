# Claude Code Harness Adapter Record

Date: 2026-09-20

## Purpose

把 Claude Code 接入 AI-VIDEO 既有工程 Harness，使其成为与 Codex 共用同一 source of truth 的一等执行 runtime。本 slice 只新增薄 adapter 与共享契约章节，不复制规则正文、不新建平行 skill 生态、不改变 Codex 路径行为。

## Current Runtime Truth

- `CLAUDE.md` 已瘦身为 14 行薄 adapter，经 `@AGENTS.md` import 承载全部 canonical 规则；原 23KB 独立副本（落后 AGENTS.md 约一个月的漂移文本）已废止。
- `.claude/settings.json` 接线 SessionStart / PostToolUse / PreCompact / Stop 四类 session-record hook，与 `.codex/hooks.json` 共用同一 `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`；既有 video-analysis PostToolUse hook 保留。
- `session_record_hook.py` 新增 `CLAUDE_WRITE_TOOL_PATH_KEYS`，识别 Claude 的 `Edit` / `Write` / `MultiEdit` / `NotebookEdit` 的 `file_path` / `notebook_path`；`apply_patch` 与 `Bash(git add)` 路径行为逐字节未变。
- `.claude/skills/` 下 7 个 symlink 指向 `.agents/skills/` 唯一实体，本 Claude 会话内已观察到 7 个项目 skill 被 runtime 热加载发现（live 证据）。
- `.claude/agents/harness-reviewer.md` 定义只读 reviewer subagent（`tools: Read, Grep, Glob, Bash`）。
- `AGENTS.md` 新增 `Agent Workflow Routing` 章节：instruction hierarchy（7 级）、T0–T3+Bug tier 路由、specs/plan/review trigger、dual independent review、verification 五级、evidence/NOT_EVALUATED、parent/worker/reviewer 角色、context control。操作细节在 `.agent/context/control-plane-playbook.md` 的 `Agent Workflow Operations`。
- Spec：`docs/superpowers/specs/2026-09-20-claude-code-harness-adapter.md`；plan：`docs/superpowers/plans/2026-09-20-claude-code-harness-adapter.md`。

## Policy Repairs Carried By This Slice

- `.claude/settings.json`（文件本身）此前不被任何 policy category 覆盖（只覆盖 `.claude/settings/*.json` 目录形式），改动会 fail safe 到 `full_tests`；已补 `control_plane` + `audit_patterns` 精确覆盖。
- HEAD（b7affb4）遗留 5 个 unmapped/unreferenced paths（`scripts/minimax_speech_batch.py`、`src/ai_video/production/minimax_speech_batch.py`、`voice_candidate.py` 及对应两个测试文件）；已补 `minimax_speech_batch` category + `minimax_speech_batch_tests` check + `full_tests.covers_check_ids` 接线。这是 pre-existing 债务修复，非本 adapter 功能，spec 与 plan 均已显式记录。

## Verification And Evidence

- Fresh passing Harness receipt（final snapshot）：`.agent/harness/runs/20260919T171918326163Z/receipt.json`；`verify-receipt` 全部标志 true（passed / fresh / fresh_for_snapshot / artifact_integrity / snapshot_matches / workspace cleanup 等）。Reviewer A 独立核验 receipt 的 `index_tree` 与实跑 `git write-tree` 逐字符相等。
- 前序 receipt：`.agent/harness/runs/20260919T171013742088Z/receipt.json`（passed）、`20260919T170758097187Z`（failed：我的 adapter 测试绝对路径断言在 detached worktree 失效 + `full_tests.covers_check_ids` 未含新 check，均已修复）、`20260919T163616749928Z`（failed：`.claude/settings.json` 未覆盖触发 fallback `full_tests` 超时）。
- `tests/test_record_ai_video_session_hook.py`：41 passed（38 既有 + 3 新增 Claude 工具测试，含越界/失败工具负向路径）。TDD 红灯先行证据：新增测试在实现前 2 failed / 1 passed。
- `tests/test_claude_code_adapter.py`：5 passed（adapter 完整性断言）。
- `policy-audit`：exit 0（unmapped / unverified / unreferenced 全 0）。`docs_contract_gate.py check`：exit 0。

## Dual Independent Review

- 同一 immutable staged target，两个独立 subagent 实例（互不见对方结论）：Reviewer A（correctness/risk）与 Reviewer B（contract compliance/acceptance/metric-substitution）。
- 第一轮：双方 `NO_BLOCKING_ISSUES`；共同 finding 为 spec 与实现机制漂移（docs-contracts.yaml 断言改由 pytest 承载但未同步）及 minimax 债务修复未记录。
- 修复后新 target 双方重审：均 `NO_BLOCKING_ISSUES`，findings 确认消除；残余 minor：`_tool_succeeded` 对未知失败形状 fail-open（方向 fail-safe）、hook 命令宿主机绝对路径耦合（与既有约定一致）、Windows symlink 退化、plan 文本滞后（已补注）。
- 注意：本轮 dual review 的两个 reviewer 均为同 runtime（Claude）隔离 context 实例，独立性强于单审但弱于跨 runtime；契约保留未来替换为 HarnessMesh 外部 reviewer 的接口。

## Live Evidence Within Claude Session

- Stop hook 在本会话真实触发 checkpoint block（capture_request_id `ai-video-record-cbf376e1233db25a`），证明 Claude 侧 Edit/Write/Bash 写入跟踪与 Stop 拦截链路工作；当时因工作未达稳定边界，按 skill 规则 acknowledge 为 `no_record` / `not_applicable`。
- `.claude/skills/` symlink 的 7 个项目 skill 在本会话中被 runtime 发现并注入可用列表（本 record 即经 `record-ai-video-session` skill 创建）。

## Remaining Risks Or Next Work

- `.claude/agents/harness-reviewer.md` 在本会话创建时无法立即以 `subagent_type: harness-reviewer` 派发（agent 类型在 session start 加载）；本轮 dual review 以 general-purpose + 内联 reviewer 规则执行。新会话中可按名派发；此点在本会话内 NOT_EVALUATED。
- `@AGENTS.md` import 在新会话启动时的实际加载（本会话启动时读的仍是旧 CLAUDE.md）：NOT_EVALUATED，建议下个新会话确认 `/memory` 或直接观察规则生效。
- `.claude/agents/kfc/`、`.claude/settings/kfc-settings.json`、`.claude/system-prompts/spec-workflow-starter.md` 为未使用的遗留 KFC 套件；本轮按 REPORT ONLY 处理，删除与否待用户单独决定。
- 本轮全部改动（含本 record）处于 staged 状态；commit 与否由用户决定。
- dual review 的跨 runtime 独立性、Stop hook 强制 harness receipt（spec 明确暂缓）为后续可选 slice。

## Agent Guardrails

- 无 Provider / paid / network / 媒体调用；验证全部为本地离线 harness 与 pytest。
- Codex 路径零改动：`.codex/hooks.json` 未动；hook 脚本对 Codex 工具路径 additive-only。
- 未触碰 `src/**`、`runs/**`、`.workflow/**` 与任何 unrelated 工作树内容。
