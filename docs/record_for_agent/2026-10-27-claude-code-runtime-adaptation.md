---
record_kind: architecture_implementation
topic_id: claude-code-runtime-adaptation
learning_eligibility: ineligible
---

# Claude Code Runtime Adaptation Record

Date: 2026-10-27

> **Supersession notice（2026-10-28）**：下文"Gate 与旧 fixture"中 `test_production_ecommerce_job_e2e.py` 7 例
> 及两例"未细分"中的 `[fail]` 例已确认为产品契约缺口并修复（`97f6161`、`639476e`、`2f8a826`），见
> [Ecommerce Commercial Performance Review](2026-10-28-ecommerce-commercial-performance-review.md)。
> 剩余基线失败为：环境 1、Architecture 1、Seedance compiler/4 1、Seedream revision 1。
> Claude 侧 session-record hooks 已按用户要求于 `d57f85b` 移除，下文所述 Claude hook 接线为历史状态。

## Purpose

用户要求 Claude Code 接手 Codex 建成的项目 skill 与 Harness，适配并可优化。
本次只处理 Agent runtime 接缝与 Harness 基线，不改 Product code、Provider、paid/credential、媒体 Gate。
紧接 [OMX Global Harness Migration](2026-10-27-omx-global-harness-migration.md)：该迁移只改了 Codex 侧。

## Current Runtime Truth

- `.claude/skills/` 以相对 symlink 暴露全部 17 个 `.agents/skills/` canonical skill（原仅 8 个）；
  `tests/test_claude_code_adapter.py` 要求两侧集合相等且全为 symlink。
- `.mcp.json` 与 `.codex/config.toml` 的 `mcp_servers` 逐字段对齐（command/args/env/cwd），
  新增 blender、gpt-image-2、codegraph、aoci、playwright。首次使用需用户在 Claude Code 批准。
- Codex blender `enabled_tools` 的 6 个白名单在 `.claude/settings.json` 以 `permissions.deny`
  表达，拒绝 `blender-mcp==1.8.7` 其余 19 个工具（Hyper3D/Hunyuan/Sketchfab/PolyHaven 等云端
  生成/下载）。测试绑定该 pin 的完整工具清单，版本升级即失败并要求重新盘点。
- `CLAUDE.md` 删除已退役的 Kimi/SUBAGENTS/`superpowers:writing-plans` 路由，新增 Runtime Term
  Mapping：Codex 角色→Claude Parent，OMX→OMC，`$skill`→Skill tool，`apply_patch`→Edit/Write，
  `image_gen.imagegen`→无对应且不得隐式替代。规则正文仍只在 `AGENTS.md`。
- `.gitignore` 忽略 `.omx/` 与 `.omc/` workflow state。OMC 按 cwd 写 `.omc/`，cwd 须留在仓库根。

## Session Work And Decisions

Commits `935edf4`、`ea8bd3e`、`450cb7c`、`807fbd5`（base `0c3be7d`）：

- Harness 基线修复：`full_tests.covers_check_ids` 补登 `authored_visual_revision_tests`、
  `reference_planning_tests`；9 个未映射 tracked 文件按 import 关系并入既有 category
  （`repair_input_admission`、`authored_visual_revision`、`production_composition_audio`），
  5 个未被引用的测试进入对应 check argv。`policy-audit` 各列表归零。
- `tests/test_distill_ai_video_learning_skill.py` 自 `a350c82`（2026-10-07）起断言已删除的
  `## Experience Learning Routing` 标题而失败；该 check 仅在 `.agents/skills/**` 变更时被路由，
  故长期未暴露。改为断言 `## Completion Standard` 内同等语义（含先 record 后 learning 顺序）。
- `record-ai-video-session` SKILL.md、`harness-reviewer.md`、open-video `creative-completion.md`
  的 runtime 专属/退役路由措辞改为双 runtime 中立。
- 选择映射表而非改写 `AGENTS.md`：constitution 13992/14000 bytes，几无预算。

## Verification And Evidence

- Related exact-range receipt passed：`.agent/harness/runs/claude-runtime-adapter-related-20261027-r4/receipt.json`
  （`0c3be7d..807fbd5`，9/9 checks；`verify-receipt` 对 r2 integrity/fresh 为 true）。
  r1 因上述陈旧断言失败，保留为历史：`claude-runtime-adapter-related-20261027/receipt.json`。
- 干净 worktree @`450cb7c` 直接运行新映射 check：`repair_input_admission_tests` 25 passed；
  `authored_visual_revision_tests` 226 passed；`production_composition_audio_tests` 1088 passed、
  23 skipped、1 failed。新加入的 4 个测试单独 17 passed。失败为
  `tests/test_production_subtitle_ass.py::test_version_mismatch_and_inexact_word_partition_fail_before_render`，
  原因是宿主 native 依赖：`libharfbuzz.so.0: undefined symbol: FT_Get_Transform` 致 libass runtime 不可用；
  属环境问题，本次未改 `src/` 或该测试，未修复、未降低断言。
- Read-only `oh-my-claudecode:code-reviewer` 审 `935edf4`：1 blocking（blender 白名单丢失）、
  2 major、5 minor，Parent 采纳并于 `450cb7c` 修复；复审 `ea8bd3e`+`450cb7c`：
  `NO_BLOCKING_ISSUES`，minor N2/N3 于 `807fbd5` 修复，N1（测试硬编码 repo root）、
  N4（deny 为 blocklist，由 pin 断言兜底）接受为残余。
- 未运行 full regression，不宣称整个项目 Harness 通过。Claude Code 对 `mcp__blender__*` deny
  的实际拦截未做运行时验证，依据为文档化 permission 语义。

## Remaining Risks Or Next Work

- 宿主 harfbuzz/freetype 符号不匹配使 libass 字幕测试失败（环境问题，干净 worktree 复现），待修环境后复跑。
- Full baseline（用户选择）已运行：`.agent/harness/runs/claude-takeover-full-baseline-20261027/receipt.json`，
  range `0c3be7d..4f153b7`，status `failed`。前 6 项 check passed；`full_tests` 13 failed、8230 passed、
  53 skipped（5166s）。本次 commits 未触及 `src/`，失败均为既有基线，未修复、未降低断言：
  - 环境（1）：`test_production_subtitle_ass.py` libass/harfbuzz `FT_Get_Transform` 符号缺失。
  - Architecture（1）：`test_architecture_gate.py` ARCH002，`src/ai_video/production/_state_commit_video.py` 超限。
  - Schema 漂移（1）：`test_ecommerce_ad_workflow_handoff.py` checked-in handoff schema 与 runtime 生成不一致。
  - 错误文案漂移（1）：`test_generation_runtime_repair.py::test_runtime_repair_requires_runtime_failure_evidence`
    期望 `durable runtime failure evidence`，实际 `Runtime repair requires durable attempt evidence.`。
  - 新 Gate 与旧 fixture（6）：`test_production_ecommerce_job_e2e.py` 多例被
    `performance_intent.character_directions.talent-presenter.acceptance` 前置要求拦截。
  - Revision Gate 与旧 fixture（1）：`test_seedream_remote_image.py` `source revision required for a changed prompt input`。
  - 未细分（2）：`test_generation_runtime_repair.py::test_cross_provider_canvas_reopen_after_paid_intent_uses_consumed_lineage`、
    `test_production_ecommerce_job_e2e.py::test_canonical_two_shot_job_closes_offline_and_replays_without_effect[fail]`。
- 机械类修复（用户选择）于 `2a61e62`：handoff schema 在干净 HEAD worktree 由 `schema_text()` 重新生成
  （排除他人 staged `composition_contracts.py`）；runtime-repair 测试改匹配 5473a4c 拆分后的首级文案，
  拒绝行为不变。复现后上述 2 个"未细分"均归入 Gate 与旧 fixture 类（Seedance compiler/4 final-text QA
  前置；performance acceptance 前置），未修，待产品判断。
  Focused receipt `.agent/harness/runs/baseline-mechanical-fixes-focused-20261027/receipt.json`（`284ddc6..2a61e62`）
  status `failed`：`generation_feedback_tests` 仅既有 cross-provider 例失败后停止。其余 focused check 于干净
  worktree @`2a61e62` 直跑：docs_contract passed、`ecommerce_ad_workflow_skill_tests` 95 passed、
  `harness_tests` 324 passed、`ecommerce_production_job_tests` 7 failed（均为既有 performance acceptance 例）。
  剩余基线失败 11 个：环境 1、Architecture 1、Gate 与旧 fixture 9。
- 审计观察（未处理，待用户决定）：policy.yaml 1847 行人工映射易持续漏登；规则文档被字节预算
  压缩影响可读性；文档标题字符串断言脆弱；Stop hook 在等待后台任务时反复要求 record 评估；
  `.claude/agents/kfc/spec-*` 的 "use PROACTIVELY" 与已退役自动 planning 冲突；
  `.agent/harness/runs` 约 335M 无清理策略；index 长期挂有其他任务 staged 内容。

## Agent Guardrails

- 新增 `.agents/skills/<x>` 必须同步 `.claude/skills/<x>` symlink；新增/修改 Codex MCP 必须同步
  `.mcp.json`（及白名单 deny），否则 `test_claude_code_adapter.py` 失败。
- Index 含他人 staged 内容时只用 `git commit -o <paths>`；`--staged` Harness 会纳入他人改动，
  改用 `harness-verify-range`。
- related/focused PASS 不代表无关 check 健康；按需路由会隐藏既有失败。

## Record And Learning Evaluation

`distill-ai-video-learning` 评估为 `no_candidate`：本次是配置适配与基线修复，非重复媒体实验。
未刷新 RAG index，未执行 Provider/媒体生成，未读取 credential。
