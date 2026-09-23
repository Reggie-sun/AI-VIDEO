# Claude Code Harness Adapter Specification

## Status

Proposed design specification。本文定义把 Claude Code 接入 AI-VIDEO 既有工程 Harness 的 contract 与 adapter 边界；它不是"为 Claude 新建一套 Harness"，也不改变 AGENTS.md 已有 product invariants、canonical ownership、verification contract 或 Provider/paid execution 规则。

本文只覆盖 agent runtime 接入层：instruction hierarchy、skill routing、specs/plan/review 触发契约、dual independent review、verification 与 evidence 契约、parent/worker/reviewer 职责、context control，以及 Claude Code 原生机制到共享契约的映射。

## Context

AI-VIDEO 已具备成熟的 runtime-agnostic Harness：

- `AGENTS.md` 是 canonical repository constitution（routing、ownership、change rules、verification contract）。
- `.agent/harness/policy.yaml` + `scripts/agent_harness.py` 是 machine-readable changed-path routing 与 receipt 验证。
- `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、`.agent/context/control-plane-playbook.md` 是 human-readable contract 层。
- `docs/superpowers/specs|plans`、`.superpowers/sdd/` 是既有 spec/plan/执行留痕约定。
- `.agents/skills/` 保存项目级 skill（含 `record-ai-video-session` 及其 `session_record_hook.py`）。
- `.codex/hooks.json` 为 Codex runtime 配置了 SessionStart/PostToolUse/PreCompact/Stop 生命周期 hook。

Claude Code 当前官方机制（v2.1.x 文档确认）：项目 `CLAUDE.md` 支持 `@path` import；`.claude/skills/`、`.claude/agents/`、`.claude/settings.json` hooks（SessionStart/PostToolUse/PreCompact/Stop 等事件名与 Codex 一致，stdin JSON payload 含 `hook_event_name`/`session_id`/`cwd`/`tool_name`/`tool_input`/`tool_response`/`stop_hook_active`）；subagent 有独立 context 且不可见主会话历史；PreToolUse deny 在任何 permission mode 下生效。

## Problem Statement

1. **规则漂移**：`CLAUDE.md` 是与 `AGENTS.md` 独立维护的滞后副本，缺 6 个整块强制规则（Per-Shot Post-Media Gate、Local ComfyUI Exemption、memory/learning routing、record-ai-video-session 完成条款、新版 paid quota、watchability 原则）。Claude 默认只读 CLAUDE.md，漂移是结构性的。
2. **Hook 不对称**：session record 的机器兜底只存在于 `.codex/hooks.json`；Claude 侧仅有 video-analysis PostToolUse hook。
3. **Hook 脚本不识别 Claude 编辑工具**：`session_record_hook.py` 只识别 `apply_patch` 与 `Bash(git add …)`；Claude 的 `Edit`/`Write`/`MultiEdit`/`NotebookEdit` 写入不会被跟踪，task-owned checkpoint 在 Claude 会话中失效。
4. **无 agent 级 dual review**：现有 acceptance 是产品 receipt 制（Per-Shot Gate、P6 FINAL_ACCEPTANCE、Harness receipt），没有"两个独立 reviewer 对同一 immutable state 审查"的 agent 工作流契约。
5. **无显式 routing 契约**：什么时候触发 specs/plan/review、加载哪个 skill，当前只靠文本自律，且 Claude 与 Codex 使用的 superpowers skill 版本门控不同（官方插件 vs Codex fork），默认行为会分叉。
6. **项目 skill 对 Claude 不可见**：`.agents/skills/` 不在 Claude Code 的 skill 发现路径内。

## Goals

1. Claude Code 成为 AI-VIDEO 现有 Harness 的一等执行 runtime，与 Codex 共用同一 source of truth。
2. 所有 routing / trigger / review / verification 契约是 **runtime-agnostic 共享契约**（AGENTS.md + playbook + machine-readable policy），Claude 侧只有薄 adapter。
3. Claude adapter 全部复用现有模块：同一 `session_record_hook.py`、同一 policy.yaml、同一 superpowers 工作流概念、同一 specs/plans 目录约定。
4. Dual independent review 成为显式 Harness contract，有确定的触发边界、immutable review target、parent adjudication 与 re-review 规则。
5. Harness routing 的关键完整性由自动化检查保证（docs-contract 断言 + harness tests），不只靠人工阅读。

## Non-Goals

- 不复制 AGENTS.md 规则到任何 Claude 专属文件；不创建第二套 skill ecosystem。
- 不修改 HarnessMesh（agent-subagent-router）代码；不引入对 HarnessMesh 的仓库依赖。
- 不改变 policy.yaml 的既有 category/check 语义；新增 coverage 仅限 Claude adapter 文件，外加一处显式记录的 pre-existing 债务修复（见 Adapter Design 表 policy.yaml 行）。
- 不引入新 runtime dependency、新 CLI、新 Provider path。
- 不为每个任务强制 specs/plan/review；routing 按 semantic risk / blast radius 分级。
- 本轮不做 Stop hook 强制 harness receipt 检查（误伤风险高，留作后续独立 slice 评估）。

## Architecture

```text
Shared contract (runtime-agnostic, single source of truth)
  AGENTS.md                     — constitution + Agent Workflow Routing（新增 compact section）
  .agent/context/control-plane-playbook.md — operational detail
  .agent/harness/policy.yaml / docs-contracts.yaml — machine-readable routing + assertions
  .agents/skills/**             — project skills（唯一实体）
  docs/superpowers/specs|plans  — spec/plan 约定
        │
        ▼  thin adapters（不得承载规则正文）
  .codex/hooks.json             — Codex adapter（已存在，不改）
  CLAUDE.md                     — Claude adapter：声明 canonical source + @AGENTS.md import
  .claude/settings.json         — Claude adapter：hook 接线
  .claude/agents/harness-reviewer.md — Claude adapter：只读 reviewer subagent 定义
  .claude/skills/*              — Claude adapter：指向 .agents/skills/* 的可见性接缝
        │
        ▼
  Claude Code runtime
```

未来接 Kimi / GPT / 其他 runtime 时，同样只新增薄 adapter，共享契约不变。

## Contract: Instruction Hierarchy

确定性优先级（高 → 低），冲突时按序裁决：

1. 用户当前明确指令。
2. 当前代码、测试与已验证 runtime evidence。
3. `AGENTS.md`（含其委托的 contract matrix、policy.yaml、playbook）。
4. Task-specific accepted spec（`docs/superpowers/specs/`）与 approved plan（`docs/superpowers/plans/`）。
5. Skill instructions（superpowers 插件、`.agents/skills/`、外部 advisory skill）。
6. Reviewer feedback（ advisory，须由 parent 裁决后落地）。
7. Runtime 默认行为（Claude Code 内建风格、插件 skill 默认门控）。

裁决规则：

- 低位阶不得推翻高位阶；skill 默认门控（第 5/7 位）与本 spec 的 routing 契约（第 3 位承载）冲突时，以 routing 契约为准。
- spec/plan（第 4 位）只对 accepted 状态下的当前 slice 生效；与 AGENTS.md 冲突时必须在同一任务中同步更新 canonical 文档，否则以 AGENTS.md 为准。
- reviewer feedback 永不直接修改 acceptance criteria。

## Contract: Task Tiers And Skill Routing

按 semantic risk / blast radius 分级，不按代码行数：

| Tier | 判据 | 必需流程 |
| --- | --- | --- |
| T0 局部低风险 | 单文件、行为可逆、无契约面变化（typo、局部 bugfix 且 root cause 明确、测试补充） | implement + targeted validation；无 specs/plan/review |
| T1 中等 | 多文件但边界清晰、behavioral change 有限、无 shared contract 变化 | （必要时 research）→ plan（writing-plans，轻量）→ implement → verify |
| T2 高风险 | architecture / workflow state machine / Provider contract / Harness 行为 / shared schema / acceptance criteria / cross-module 行为变化 | research → specs → plan → implement → verification → implementation review |
| T3 关键契约 | canonical ownership、verification contract、paid/credential/recovery/QA acceptance 语义变化 | T2 全部 + dual independent review |
| Bug | 任何 tier 的 bug | systematic-debugging 先行（root-cause 分析）→ 按 tier 走对应流程 → regression validation |

Skill 路由（命中即触发，不预载全部）：

- 设计/需求不清 → `superpowers:brainstorming`。
- 写 plan → `superpowers:writing-plans`（plan 落 `docs/superpowers/plans/YYYY-MM-DD-<slug>.md`，遵循仓库既有格式）。
- 执行已批准 plan → `superpowers:executing-plans` 或 `superpowers:subagent-driven-development`。
- Bug → `superpowers:systematic-debugging`。
- 声称完成前 → `superpowers:verification-before-completion`。
- 到达 review 边界 → 本 spec 的 reviewer 机制（`.claude/agents/harness-reviewer.md` / Codex 等价物）。
- AI-VIDEO 项目 skill（`.agents/skills/`）按 AGENTS.md 既有 routing 表触发。
- Creative skill（hell-grind/higgsfield/video-shotcraft 等）仍按 AGENTS.md Creative Skill Routing，advisory only。

## Contract: Specs Trigger

必须创建或更新 spec（落 `docs/superpowers/specs/`，含 Status 头）的情形：

- architecture contract / canonical ownership 变化；
- workflow state machine 或 lifecycle 语义变化；
- Provider contract、renderer、timeline、activation owner 变化；
- Harness 行为变化（routing、verification、review、hook 语义）；
- acceptance criteria 或 Shot generation/regeneration policy 变化；
- shared schema / Manifest / artifact layout 变化；
- persistent project rule 变化（AGENTS.md / playbook 级别）；
- cross-module 行为变化；
- 用户明确要求 specs。

普通小修复、文档措辞修订、测试补充不触发 specs。spec 是 proposed contract，不得把未实现行为描述成 runtime truth。

## Contract: Plan Trigger

满足任一条件即触发 plan（复用 `superpowers:writing-plans`，不重新实现）：

- 多文件修改且顺序/依赖非显而易见；
- 多阶段实施或需要交接/委派；
- T2/T3 任务；
- architecture / Provider / workflow 修改；
- 涉及迁移、回滚或兼容性设计。

Plan 必须基于已 accepted 的 spec（或本任务内同步产出）与既有约束；无占位符；每个 milestone 有 Files/Contract/Acceptance/Verification。T0/T1 简单任务不产 plan artifact。

## Contract: Review Trigger And Boundaries

Review 只在有完整、稳定 review target 的边界触发：

1. **Spec review**：T2/T3 的 spec 完成后、进入 plan 前。
2. **Plan review**：T2/T3 的 plan 完成后、进入 implementation 前（可用 writing-plans 的 plan-document-reviewer 模式）。
3. **Implementation review**：T2/T3 implementation 到达完整 checkpoint（diff 稳定、对应验证通过）后。
4. **Final dual review**：T3 任务在声明完成前。
5. T0/T1 不触发独立 review（T1 可由 parent 自行复核）。

禁止"写一点 → review → 改一点 → review"循环；每次 review 必须针对新的完整 target。`review executed` / `PARSED` 不等于 `accepted`。

## Contract: Dual Independent Review

T3（及 parent 判定需要的高风险 spec/plan）采用双独立审查：

- 两个 reviewer 针对**同一 immutable review target**（exact commit 或 exact staged snapshot，target ID 记录于审查证据）独立审查。
- 两个 reviewer 互不先看对方结论（独立 context，不共享历史）。
- 双方都无 blocking issue 才允许 acceptance；不采用多数票；不允许一方因另一方意见迁就。
- 冲突由 parent 调查具体 evidence 裁决；reviewer 不修改 acceptance criteria。
- 修复后生成**新的** review target，两个 reviewer 必须基于同一新状态重新审查。
- 当前实现：两个独立 Claude reviewer subagent 实例（`.claude/agents/harness-reviewer.md`，read-only 工具集），分别以 correctness/risk 视角与 contract/compliance 视角派发。契约保留替换为跨 runtime reviewer（如 HarnessMesh 资格化的外部 reviewer）的接口；替换时无需修改本契约其余部分。

## Contract: Verification Levels（禁止 metric substitution）

声称完成前必须区分五级，不得以下位替代上位：

1. **Execution success**：命令 exit 0、API 请求成功、schema parsed。
2. **Structural validity**：类型/格式/引用完整。
3. **Functional correctness**：行为符合实现意图（测试覆盖 public behavior、boundary、failure path）。
4. **Acceptance criteria**：spec/plan 的验收条件逐条有证据。
5. **Final review acceptance**：到达 review 边界且通过规定级别的 review。

AI-VIDEO 特有：局部机器指标（如"动作在 1.5 秒内到位"）不能替代最终成片目标（"完整镜头正常速度下自然完成动作且无冻结/跳帧/身份漂移/视觉破坏"）。代码或 executable tooling change 完成前必须有 fresh passing Harness receipt（既有 verification contract 不变）。

## Contract: Evidence-Based Completion

- 所有 PASS / DONE / ACCEPTED 必须附 evidence（命令、输出摘要、receipt 路径、target ID）。
- 无法验证的项必须明确标 `NOT_EVALUATED`，不得猜测为 PASS。
- 未执行的 live/provider/media/quality 验证必须显式标注。

## Contract: Parent / Worker / Reviewer Responsibilities

- **Parent**（主会话）：理解用户最终目标；按 routing 契约决定是否触发 research/specs/plan/review；分派任务；裁决 reviewer disagreement；唯一能做最终 acceptance 判断的 agent 角色。
- **Worker**（implementer subagent 或主会话实施态）：实施具体任务；不得自行降低 acceptance criteria；不得绕过 verification。
- **Reviewer**（独立 subagent）：read-only 优先；输出 evidence + severity；不继承主会话历史；不负责让任务通过。

## Contract: Context Control

- 常驻 context 仅限：用户全局规则、CLAUDE.md（薄 adapter）、AGENTS.md（经 import）、skill descriptions。
- skill 正文、spec、plan、provider docs、workflow docs、playbook 细节全部按需加载（progressive disclosure）。
- 禁止把整个仓库文档或全部 skill 永久塞入 context；compact 后由 hook 重注入关键 checkpoint 信息。

## Claude Adapter Design

| 文件 | 动作 | 职责 | 复用来源 |
| --- | --- | --- | --- |
| `CLAUDE.md` | MODIFY（瘦身重写） | 声明 canonical source、语言/执行偏好、最小 runtime 差异说明；`@AGENTS.md` import 承载全部规则 | 复用 AGENTS.md 全文 |
| `.claude/settings.json` | MODIFY | 增加 SessionStart/PostToolUse/PreCompact/Stop 的 session-record hook 接线；保留现有 video-analysis hook | 复用 `.codex/hooks.json` 同一脚本与语义；PostToolUse matcher 适配 Claude 工具名（`Edit\|Write\|MultiEdit\|NotebookEdit\|Bash`） |
| `.agents/skills/record-ai-video-session/scripts/session_record_hook.py` | MODIFY（最小扩展） | `_task_owned_paths` 增加对 Claude `Edit`/`Write`/`MultiEdit`/`NotebookEdit` 的 `file_path` 识别；Codex 路径行为不变 | 同一脚本，双 runtime 共用 |
| `tests/test_record_ai_video_session_hook.py` | MODIFY | 覆盖新工具名的 owned-path 提取与既有行为回归 | 既有测试文件 |
| `tests/test_claude_code_adapter.py` | CREATE | adapter 完整性断言（CLAUDE.md import、settings.json hook 接线、hook 脚本常量、reviewer 只读、skill 接缝单一实体）；经既有 `harness_tests` check 强制执行 | 替代 docs-contracts.yaml 断言方案——复用既有 check 路由，零新增 check 定义 |
| `.claude/agents/harness-reviewer.md` | CREATE | 只读 reviewer subagent（tools 限 Read/Grep/Glob/Bash 只读 + agent_harness inspect/verify-receipt；description 驱动主动委派；独立 context） | 复用 superpowers requesting-code-review 的 reviewer 模板思想与 contract matrix 的验证入口 |
| `.claude/skills/<name>` | CREATE（可见性接缝） | 使 `.agents/skills/` 的 7 个项目 skill 对 Claude 可发现；首选 symlink（单一实体），若 Claude Code 不跟随 symlink 则改为仅含 frontmatter + `@` 引用的薄 wrapper | 复用 `.agents/skills/*` 实体，不复制正文 |
| `AGENTS.md` | MODIFY | 新增 compact "Agent Workflow Routing" 章节：instruction hierarchy、tier 表、specs/plan/review trigger、dual review、verification 五级、parent/worker/reviewer、context control；指向 playbook | 承载本 spec 的共享契约 |
| `.agent/context/control-plane-playbook.md` | MODIFY | routing/review 的 operational detail（review target 构造、reviewer 派发模板、adjudication 步骤） | 既有 playbook 结构 |
| `.agent/harness/policy.yaml` | MODIFY（最小） | audit_patterns 与 control_plane category 补充 `CLAUDE.md`、`.claude/settings.json`（既有漏覆盖）、`.claude/agents/**`、`.claude/skills/**` coverage；`harness_tests` argv 追加新测试文件。另含一项 pre-existing 债务修复：为 HEAD 中未被任何 category 覆盖的 `minimax_speech_batch` / `voice_candidate` 共 5 个已提交文件（b7affb4 引入）补最小 category + check + `full_tests.covers_check_ids` 接线——不补则 policy-audit 对所有后续 scope 失败，本 slice 无法取得 fresh receipt | 既有 category，复用 `harness_tests` |
| `.claude/agents/kfc/**`、`.claude/settings/kfc-settings.json`、`.claude/system-prompts/spec-workflow-starter.md` | REPORT ONLY | 未使用的遗留 KFC 套件；本轮不删除，仅报告，待用户单独决定 | — |
| `src/**`、`runs/**`、`.workflow/**`、用户未提交改动 | DO NOT TOUCH | — | — |

## Compatibility And Rollback

- Codex 路径零变化：`.codex/hooks.json` 不动；hook 脚本扩展只增不改（`apply_patch`/`Bash` 路径行为逐字节保持）。
- AGENTS.md 新增章节为 additive；既有章节不动。
- CLAUDE.md 瘦身不改变规则语义（规则正文全部由 import 承载）。
- 回滚 = 还原上述文件；无持久化 state、无 schema migration。

## Acceptance Criteria

1. CLAUDE.md 为薄 adapter，`@AGENTS.md` import 生效，AGENTS.md 全部规则对 Claude 会话可见。
2. `.claude/settings.json` 四类 session-record hook 接线完成；Claude 会话中 Edit/Write 写入能被 hook 跟踪并触发 checkpoint（有测试证据）。
3. Codex hook 行为回归通过（`test_record_ai_video_session_hook.py` 全绿）。
4. `.claude/agents/harness-reviewer.md` 可被派发，工具集 read-only。
5. 7 个项目 skill 在 Claude 中可发现（单一实体，无正文复制）。
6. AGENTS.md 新章节承载全部 routing/review/verification 契约；policy.yaml 覆盖新增 adapter 文件；docs-contracts 断言通过。
7. `policy-audit` 无 unmapped/unverified paths；Harness receipt fresh passing（control_plane scope）。
8. Dual review 契约可按文档执行：同一 immutable target、两个独立 reviewer、parent adjudication、修复后新 target 重审。

## Verification

- `make harness-verify`（staged scope：control_plane + harness_control → harness_tests）。
- `scripts/agent_harness.py policy-audit`。
- `python scripts/docs_contract_gate.py check`（既有断言回归；adapter 完整性断言由 `tests/test_claude_code_adapter.py` 承载并经 `harness_tests` 强制执行）。
- `python -m pytest tests/test_record_ai_video_session_hook.py -q`。
- Claude 侧手动冒烟：新会话确认 AGENTS.md 规则加载、skill 可发现、hook checkpoint 触发（作为 NOT_EVALUATED 标注项若本轮无法自动证明）。
