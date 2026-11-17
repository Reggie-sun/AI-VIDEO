# Skill And Agent Routing

## Runtime Evidence

2026-11-16 本机版本为 Claude Code 2.1.325、codex-cli 0.169.0。Claude 的 `skills` frontmatter 会在子代理启动时注入完整 Skill；本项目改为角色内 Read exact `.agents/skills/<name>/SKILL.md`，避免无条件注入。官方语义见 [Claude subagents](https://code.claude.com/docs/en/sub-agents) 与 [Claude skills](https://code.claude.com/docs/en/skills)。配置变更并不证明真实选择成功；Token、延迟、自动触发率及权限拒绝实测均为 `NOT_EVALUATED`。

Codex 使用现有 OMX 原生角色，不要求把 Claude frontmatter 翻译成另一套配置。项目职责来源仍是下表指向的角色文件与 canonical owner。Codex 自定义 Agent 配置见 [Codex subagents](https://developers.openai.com/codex/subagents)；子代理继承父会话的权限边界，提示词中的只读声明不形成沙箱，不把未验证的 `sandbox_mode` 覆盖当强制隔离证据。

## Shared Responsibilities

| Project responsibility | Claude project agent | Codex native role | Skill loading / output |
| --- | --- | --- | --- |
| Blender 本地制作 | `blender-artist` | `executor` | 轻量入口 `docs/blender-routing.md`；执行前 expert protocol，再按需要 blockout / animation / rigging / previs；返回 exact 资产与验证限制 |
| 提交前连续性 | `continuity-supervisor` | `verifier` | 读取 existing continuity references 与 canonical Gate；返回五项证据，不创作或提交 |
| exact MP4 逐镜 Gate | `shot-gate-reviewer` | `verifier` | 读取 Per-Shot Gate；仅 sealed selected H3 才读取 H3 §F；逐项 verdict |
| 官方及社区调研 | `model-researcher` | `researcher` | 需要记忆时由 memory 执行 lane 提供结果；返回可追溯来源与适用边界 |
| 检索 / 记录 / 提炼 | `memory-keeper` | `executor` | 当前阶段分别读取 retrieve / record / distill；稳定记录后自动评估 learning，不启动时全载 |
| Harness 验证 | `harness-runner` | `verifier` | 执行 exact snapshot 与 level 的 Harness，返回 receipt；允许本地验证 artifact 写入 |
| 显式独立审查 | `harness-reviewer` | `code-reviewer` | 仅用户显式要求此项目 reviewer 时；读取 immutable target 与已有证据 |

主会话在 dispatch 中给出任务、selected Provider（如适用）、exact 输入/identity、允许的输出路径、验收项、当前 evidence 与 scope。Codex role 必须由实际原生角色面选择，再读取对应 `.claude/agents/<name>.md` 的职责正文作为任务材料；该文件不会自行改变 Codex tools 或 sandbox。角色不可用时按原 Gate 报 `NOT_EVALUATED`，不得伪造已执行或静默转为主会话代做。

## Tool Boundaries

Claude observer 四角色（continuity、shot Gate、researcher、harness reviewer）显式移除 Bash、写工具、Skill 和 Agent 工具；按需通过 Read 读取文档，避免 Skill 的工具扩展成为旁路。continuity 与 shot Gate 仅保留 video-analysis 的 `video_probe`、`video_extract_frames`、`video_transcribe`、`video_scene_detect` 精确工具名取证；禁止 wildcard、optimization 与可选择远程音频执行的 composite 工具。需要远程音频理解时，由主会话通过已授权 canonical 执行 lane 提供证据，缺失仍为 `NOT_EVALUATED`；MCP 可能产生本地分析缓存，故这里的只读指不提供任意 shell / 文件编辑能力，不宣称整个服务进程零写入。

需要 hash、lint、receipt 验证、tests 或有 derived-index 维护的 memory query 时，由主会话派授权执行 lane，返回绑定 exact 输入的新鲜输出。observer 保留最终证据检查；缺失、过期、身份不符仍是 `NOT_EVALUATED`。Harness runner、memory keeper、Blender artist 是有界执行角色，保留必要 Bash/写工具；Prompt 范围约束不等于强制沙箱。Codex 原生 observer 若没有实际可验证工具限制，只能报告其权限隔离未验证，不沿用 Claude allowlist 的证明。

Production state、付费/远程提交、最终整合、commit/push 与验收仍由 `AGENTS.md` 及 matrix 的唯一 Owner 控制。Provider Skill 只在 selected Provider 已明确后读取；I2V/T2V 等术语不选择 Provider。创作主线仍由主会话使用现有创作 Skill，不迁入新角色。

## Verification

`tests/test_claude_code_adapter.py` 检查发现、symlink、预载与 tools 契约；`scripts/skill_routing_eval.py` 提供案例契约及显式 observation 评分。静态检查不能证明 CLI 真实自动调用或权限拒绝。环境检查只诊断当前路径与能力，不启动 MCP、不读 secret、不修改启动方式；Windows symlink checkout 需在真实平台验证后才能宣称兼容。
