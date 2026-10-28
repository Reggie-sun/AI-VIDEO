---
record_kind: session_summary
topic_id: omx-global-harness-migration
learning_eligibility: ineligible
---

# OMX Global Harness Migration Record

Date: 2026-10-27

## Scope And Current Runtime

用户要求全局安装 Oh My Codex，并将冲突的既有 Harness 编排规则改为 OMX。
本机原有 `oh-my-codex@0.21.26` CLI，但没有完成 user setup；已从官方 npm package
升级至 `0.21.38`，实际执行 `omx setup --scope user --legacy --force`。
交付模式为 legacy，Team surface enabled，MCP mode 为 none；既有用户 MCP 保留。
官方入口为 [Yeachan-Heo/oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex)。

全局 `~/.codex/AGENTS.md` 使用 OMX generated contract，并将中文、原生 Agent、
owned-path 写入、当前 working tree 和 Product 安全约束保留在官方支持的
`USER:OMX:POLICY` block。`~/AGENTS.md` 的旧角色路由改为 OMX；
`~/.codex/SUBAGENTS.md` 只保留兼容指针，不再维护另一套 profile/Risk Gate。
安装了 32 prompts、24 OMX skills、18 native roles；旧非冲突 skills/profiles 未卸载。
32 个 legacy `~/.agents/skills` 重名目录已归档，唯一目录与 canonical skills 保留。

## Conflict Resolution

- 全局与项目 `hooks.json` 的非标准根字段 `description` 会使 OMX setup 拒绝执行，已删除。
  全局非标准 `Interrupt` event 已随备份退役，其 ORCA handler 的其他有效事件保留。
  OMX setup 合并其 native hooks，既有合法 foreign hooks 保留。
- 项目 `AGENTS.md` 和 playbook 的自动 Superpowers planning、旧 SUBAGENTS
  profile/review 路由退役；Agent workflow 归全局 OMX 和当前安装的 OMX Skills。
- Harness 继续提供测试、exact snapshot 和 receipts，不调度 Agent。
  `runtime_skill_calls = 0` 仍约束 Production；OMX 仅管理 Agent workflow state。
- 未改变 Product code、Harness policy、Provider/paid/unknown gates 或媒体人工验收。
  原模型、model providers、登录存储、8 个全局 MCP、插件、marketplaces、信任项目、
  skills 配置、approval/sandbox、memories 和既有 features/tui 设置均与备份逐项比对保留。

## Verification And Limits

- 全局 `omx doctor`：19 passed、1 warning、0 failed；native hook dist smoke 通过，
  无重复 skill。warning 表明本对话不是 OMX-managed session，不代表安装损坏。
- 项目目录 `omx doctor`：18 passed、2 warnings、0 failed；另一个 warning 是项目
  `.omx/state` 尚未创建。未伪造 session binding；新交互会话从项目目录运行 `omx`。
- 一次真实 `omx exec` 安装 smoke 调用成功，exit 0 且响应严格为 `OMX-EXEC-OK`；
  cwd 为独立临时目录，无工具调用、子代理或 Product 媒体生成。
- `agent_rules_gate`、`docs_contract_gate check --json` 与 owned diff whitespace 检查通过；
  规则、docs contract、runtime skill boundary 相关测试 69 passed；open-video 测试 48 passed。
- 直接 Harness suite 为 319 passed、2 failed。旧 policy 的 `full_tests.covers_check_ids`
  缺 `authored_visual_revision_tests` / `reference_planning_tests`，并有 9 个既有 tracked
  source/test paths 未映射。已重开 HEAD，核验 policy、失败测试、audit 实现和这 9 个文件
  均与 HEAD 原字节相同；两项为基线问题，未扩围修复或降低断言。
- 原 `AGENTS.md` 已超过 14,000-byte 上限；压缩本次替换的编排文字后恢复预算通过，
  未放宽 budget。未运行 full regression，不宣称整个项目 Harness 已通过。

Canonical focused/related exact-range receipts 使用
`.agent/harness/runs/omx-global-focused-20261027/receipt.json` 与
`.agent/harness/runs/omx-global-related-20261027/receipt.json`；以实际 receipt 结果为准。
安装、真实 smoke、归档清单及配置保存核验留在本地
`/home/reggie/.local/state/omx-migration/20261027T235321Z/`；private backup 不进入 Git。
本记录所在提交仅发布 owned 项目规则和历史 notice，全局安装/config 不由 repository Git 发布。

## Record And Learning Evaluation

按 `record-ai-video-session` 记录；`distill-ai-video-learning` 评估为 `no_candidate`：
本次是配置迁移，不是重复媒体实验或 controlled comparison，不创建 Learning Claim。
未刷新 RAG index；未读取/复制 auth 文件，未执行 Product Provider generation。
工作区原有 unrelated dirty/staged 内容保留，旧失败及历史 receipts 不改判为 PASS。
