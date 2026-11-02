---
record_kind: architecture_implementation
topic_id: claude-domain-role-subagents
learning_eligibility: ineligible
---

# Claude Domain Role Subagents Record

Date: 2026-11-02

## Purpose

用户要求为项目配置“各有职责、skill 与 description”的子代理，并确认只配 Claude Code、
只产出建议与草稿权限，且问及是否与 oh-my-claudecode（OMC）agents 冲突。

## Session Work And Decisions

- 在 `.claude/agents/` 新增 13 个领域专职角色：`video-director`、`drama-writer`、
  `ad-strategist`、`reference-artist`、`blender-artist`、`provider-prompt-author`、
  `continuity-supervisor`、`shot-gate-reviewer`、`sound-designer`、
  `motion-graphics-editor`、`memory-keeper`、`model-researcher`、`harness-runner`。
  原 `harness-reviewer` 与 `kfc/` spec agents 未改动。
- 每个角色用 frontmatter `skills` 预载所属项目 skill（全部 17 个 canonical skill 各有归属），
  `tools` 为显式 allowlist；付费/外部生成 MCP（`elevenlabs-direct`、`minimax-direct`、
  `gpt-image-2`）不在任何角色内。场记、逐镜 Gate、调研、Harness 执行四个角色只读。
- 权限按用户选择：子代理只出建议与草稿；付费/远程提交、Production state、commit/push 归主会话。
  Parent 判断例外：`blender-artist` 可操作本机 loopback Blender MCP 产出场景草稿，
  `motion-graphics-editor` 可本机离线渲染开发预览；两者均非 Production 激活。
- 与 2026-10-27 [OMX 迁移](2026-10-27-omx-global-harness-migration.md) 的关系：退役的是旧
  SUBAGENTS profile/Risk Gate review 路由；本次角色是 OMC workflow 内可派发的领域 worker，
  代码实现、规划、代码 review/verify 仍走 `oh-my-claudecode:*`。分工写在 `CLAUDE.md`
  Claude Runtime Notes。OMC agents 均带 `oh-my-claudecode:` 插件前缀，与项目角色无重名。
- 未修改 `.codex/`（含用户未提交的 patchright 改动），Codex 侧无对应角色。

## Verification And Evidence

- `tests/test_claude_code_adapter.py` 新增两项：角色身份/description/显式 tools/无付费通道/只读角色无写工具；
  每个项目 skill 恰被某角色预载。变异检查：删一个 skill 归属或加入 ElevenLabs 工具时各自失败，还原后 10 passed。
- 一次 headless `claude -p --model haiku` 载入核验：13 个角色均可见，debug log 中项目 agent 文件无
  unrecognized-key 警告（仅 OMC 插件自身 `level` 键既有警告）。
- Focused Harness：`.agent/harness/runs/claude-role-agents-focused-20261102b/receipt.json`，326 passed。
  未跑 related/full，不宣称完整回归。

## Remaining Risks

- 各角色尚未在真实制作任务中派发；description 的自动路由效果与预载 skill 的上下文占用
  （`blender-artist` 预载约 90KB）未经实际任务检验。
- 新增项目 skill 时须同步指派角色，否则 adapter 测试失败。

## Record And Learning Evaluation

`distill-ai-video-learning`：`no_candidate`（配置变更，无重复媒体实验或对照）。未刷新 RAG index。
