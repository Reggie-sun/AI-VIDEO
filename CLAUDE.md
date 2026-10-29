# AI-VIDEO Claude Code Adapter

本文件是 Claude Code runtime 的薄 adapter，不是规则正文。Canonical source of truth 是 `AGENTS.md`，经下方 import 全量加载。

禁止在本文件复制或改写规则正文；任何规则修改只改 `AGENTS.md` 及其委托文档（`docs/agent-primary-contract-matrix.md`、`.agent/harness/policy.yaml`、`.agent/context/control-plane-playbook.md`）。本文件若与 `AGENTS.md` 冲突，以 `AGENTS.md` 为准。

@AGENTS.md

## Claude Runtime Notes

- Claude 侧不注册 session-record hooks（用户 2026-10-28 要求移除）；仅 `.codex/hooks.json` 接线。Claude 下 record/learning 评估按 `AGENTS.md` Completion Standard 主动执行，无 hook 不免除。
- 项目 skill 唯一实体在 `.agents/skills/`；`.claude/skills/` 只是逐一指向它们的 symlink 接缝，新增 skill 须同步建链（`tests/test_claude_code_adapter.py` 校验全量对齐），不得在 `.claude/skills/` 维护第二份正文。
- Project MCP 在 `.mcp.json`，与 `.codex/config.toml` 的 `mcp_servers` 同名对齐；首次加载需用户在 Claude Code 中批准。Codex `enabled_tools` 白名单在 `.claude/settings.json` 以 `permissions.deny` 表达；Codex 的 per-server timeout 无对应字段，由 Claude 全局 MCP timeout 承担。可用不等于授权，外部效果仍按 `AGENTS.md` 判定。
- 保持 cwd 在仓库根：OMC 按 cwd 写 `.omc/` 状态，`cd` 进子目录会生成游离 `.omc/`。
- `.claude/agents/harness-reviewer.md` 仅为用户显式要求时的只读 reviewer 定义，不主动派发。
- Specs / plans 约定：`docs/superpowers/specs|plans/YYYY-MM-DD-<slug>.md`。

## Runtime Term Mapping

`AGENTS.md` 已用中性术语（主会话 / 子代理 / 编排层）；playbook 与 Skill 仍以 Codex 术语书写，Claude Code 下按此表读取，职责、授权与 Gate 不变。

| Codex 术语 | Claude Code 对应 |
| --- | --- |
| Codex / Native Codex / Codex Parent（作为角色） | 当前 Claude 主会话（Parent） |
| Codex 原生 Agent / 子代理 | Agent tool 的内置与 `oh-my-claudecode:*` 子代理 |
| 全局 OMX（`~/.codex/AGENTS.md` 与 OMX Skills） | 全局 OMC（`~/.claude/CLAUDE.md` 与 `oh-my-claudecode:*` Skills） |
| `$plan` / `$autopilot` / `$ultragoal` / `$team` | `/oh-my-claudecode:plan` / `autopilot` / `ultragoal` / `team` |
| `$<skill>`（如 `$record-ai-video-session`） | Skill tool 调用同名项目 skill |
| OMX `code-reviewer` / `verifier` | `oh-my-claudecode:code-reviewer` / `oh-my-claudecode:verifier` |
| `apply_patch` | `Edit` / `Write` / `MultiEdit` / `NotebookEdit` |
| `.omx/` workflow state | `.omc/` workflow state（不进 Git，不拥有 Product state） |
| Codex Generated Image（`image_gen.imagegen`） | 无对应；默认入口不可用，其他已授权入口按 playbook 显式选择，不视为默认替代 |

`omc ask` 与外部 CLI 委派（Codex/Gemini 等）属外部 Agent，按 [Implementation Review](.agent/context/control-plane-playbook.md#implementation-review) 处理。
