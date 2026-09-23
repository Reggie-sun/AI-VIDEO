# AI-VIDEO Claude Code Adapter

本文件是 Claude Code runtime 的薄 adapter，不是规则正文。Canonical source of truth 是 `AGENTS.md`，经下方 import 全量加载。

禁止在本文件复制或改写规则正文；任何规则修改只改 `AGENTS.md` 及其委托文档（`docs/agent-primary-contract-matrix.md`、`.agent/harness/policy.yaml`、`.agent/context/control-plane-playbook.md`）。本文件若与 `AGENTS.md` 冲突，以 `AGENTS.md` 为准。

@AGENTS.md

## Claude Runtime Notes

- Session-record hooks 接线在 `.claude/settings.json`，与 `.codex/hooks.json` 共用同一 `.agents/skills/record-ai-video-session/scripts/session_record_hook.py`。
- 项目 skill 唯一实体在 `.agents/skills/`；`.claude/skills/` 只是指向它们的可见性接缝（symlink），不得在 `.claude/skills/` 维护第二份正文。
- 独立 reviewer subagent 定义在 `.claude/agents/harness-reviewer.md`；dual review 的触发边界与裁决规则见 `AGENTS.md` 的 `Agent Workflow Routing`。
- Specs / plans 约定：`docs/superpowers/specs|plans/YYYY-MM-DD-<slug>.md`；plan 编写复用 `superpowers:writing-plans`。
