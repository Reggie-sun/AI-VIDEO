---
record_kind: architecture_implementation
topic_id: agents-constitution-routing
learning_eligibility: ineligible
---

# AGENTS Constitution Routing Phase 1 Record

> **Update（2026-10-28）**：第 2、3 步已完成（`b020b11`），见下文 "Phase 2 And 3"；原 "第 2、3 步未做" 为历史状态。

Date: 2026-10-28

## Purpose

用户认为 `CLAUDE.md` 有问题但难以表述，本次先诊断规则文件结构，再按用户选择完成第 1 步：把制作细则移出常驻
`AGENTS.md`，只留路由行。规则语义不变；不涉及 Product code、Provider、paid/credential 或媒体 Gate。

## Diagnosis

用户在列出的问题中确认三项：

1. `AGENTS.md` 以 Codex 术语书写，Claude 依赖 `CLAUDE.md` 的 Runtime Term Mapping 转译。
2. 常驻 constitution 自称只放 authority/安全/owner/completion，实际混入 720p、字幕标点、纯中文提示词、
   人物身份参考等制作细则。
3. 句子被压成术语串，人难读、难改。

根因证据：

- 字节上限逼出压缩：`.agent/harness/agent-rules.yaml` 限 `AGENTS.md` 14000 bytes，改前 13992；playbook 限
  18000 bytes / 210 行，现 17681 bytes / 206 行，两者都无法再吸收规则。
- 规则持续回涨：[2026-10-07 trim](2026-10-07-agent-guide-trim.md) 把 `AGENTS.md` 压到 11481 bytes，三周内经约
  20 次加规则提交回到 13992；其中 `3e0ae8e`（纯中文）、`7a95b0c`（身份参考）、`9a76b99`（字幕时机）只改了
  `AGENTS.md`，`7081ed5`（句尾标点）在仓库内只额外写入一份单作品 artifact。
- 用户确认这些制作规则当初是顺手加入常驻层，并非因 Skill 中不被执行而升级，可以移出。

另一项已核实但用户未选择、本次未处理的问题：当前 ccam profile `work2` 只安装 `ccam` 插件，会话中没有任何
`oh-my-claudecode:*` agent/skill，但 `~/.claude/CLAUDE.md`（OMC 指令）仍被加载，项目 `CLAUDE.md` 也把
reviewer/verifier 映射到 `oh-my-claudecode:*`；profile 内 `CLAUDE.md` 是指向不存在的
`groups/default/CLAUDE.md` 的断链。

## Session Work And Decisions

commit `69eaa9b` 只改两个文件：

| 原 `AGENTS.md` 内容 | 现归属 |
| --- | --- |
| 图像/视频提示词纯中文 | `docs/canvas-continuous-production.md#prompt-language-and-character-identity`（新节，原文搬移） |
| 人物身份参考先读 `referces/README.md` | 同上 |
| 字幕句尾不加符号 | `docs/canvas-continuous-production.md` Formal Narrative Output Defaults 逐镜字幕句 |
| 原片认可后再做字幕、逐镜累积审看 | 该文档已有，`AGENTS.md` 改为路由 |
| 商品广告固定 720p | 该文档与 `ecommerce-ad-workflow` 已有，`AGENTS.md` 改为路由 |
| 拼接审查与复用素材核验 | `open-video`（HEAD 中 `references/creative-completion.md` 已有）；`AGENTS.md` 保留"单段认可不豁免拼接审查" |
| 白模不默认、参考选择依据 | `docs/canvas-production-harness.md#per-shot-whitebox-reference` 已有；`AGENTS.md` 保留一句原则 |
| 摄影服从叙事、分组定长、不冻结机位 | `open-video`（`SKILL.md`、`references/event-led-timing.md`）已有 |

有意保留原文：

- Per-Shot Post-Media Gate：硬门槛，`test_ecommerce_ad_workflow_skill.py` 断言其在 `AGENTS.md` 节内的措辞。
- Empirical Validation Priority：playbook `#empirical-uncertainty-triage` 已完整覆盖，但属于工作方法原则，留待第 3 步。
- Community Reference And Workflow Improvement：仓库内没有其他通用归属，留待第 3 步。

结果：`AGENTS.md` 130 → 118 行、13992 → 12966 bytes；`docs/canvas-continuous-production.md` 17656 → 18191 bytes（无上限登记）。

## Verification And Evidence

- 改动前确认被路由的细则存在于 HEAD 版本，而非仅存在于其他会话的未提交改动中。
- `python -m scripts.agent_rules_gate`：ok（含新锚点与 `../referces/README.md` 链接）。
- 断言 `AGENTS.md` 措辞的测试与 `test_agent_rules_gate.py`、`test_claude_code_adapter.py`：45 passed。
- Harness focused（commit range `80f71fd..69eaa9b`）：`docs_contract_check` passed、`harness_tests` 324 passed；
  receipt `.agent/harness/runs/20261029T004822095249Z/receipt.json`（gitignored，仅本地）。
- 只跑了 focused 级别，未跑 related/full。
- 已 push，远端 `main` = `69eaa9b7c4e7a15d6ac40079bfc6650c3a305dbd`。

## Phase 2 And 3 — 2026-10-28

同日完成第 2、3 步，commit `b020b11`，只改 `AGENTS.md`、`CLAUDE.md`、`.agent/harness/agent-rules.yaml`：

- 第 2 步：前言定义中性术语「主会话」（Parent）、「子代理」、「编排层」（Codex 为 OMX，Claude Code 为 OMC）；
  "Creative intent 归 Codex"、"全局 OMX"、"仅用 Codex 原生 Agent"、"OMX 只管理 Agent workflow state" 改为中性表述。
  `CLAUDE.md` 映射表不缩减：playbook 与多个 Skill 仍用 `$plan`、`全局 OMX`、`Native Codex`、`apply_patch` 等词，
  只把适用范围说明改为"`AGENTS.md` 已中性；playbook 与 Skill 仍以 Codex 术语书写"。
- 第 3 步：各节改写为白话并补必要的"为什么"；章节标题保留，`<!-- aoci:begin/end -->` 块未改；
  "Community Reference And Workflow Improvement" 并入 "Empirical Validation Priority"（两节重叠，仓库内仅历史 record 以文字提及）。
  测试断言的原文短语保留在新句子里，未改测试。
- 字节上限：白话版约 14100 bytes，超出 14000；三轮逐句压缩收效很小（中文每字 3 bytes），继续压只能删"为什么"，
  余量会再次归零。用户选择把 `AGENTS.md` 上限从 14000 提到 16000。结果 153 → 155 行、12966 → 14684 bytes。

## Phase 2 And 3 Verification

- 独立 reviewer（`oh-my-claudecode:critic`，只读）按新旧条款逐条比对：首轮 REQUEST_CHANGES，6 MAJOR + 11 MINOR，
  均为压缩措辞导致的义务丢失或条件收窄/放宽（如 snapshot/receipt 义务、Empirical 合并后的触发范围、
  "unrelated" 被写成"别人"、development worktree、No-regression 只剩修复、付费授权去掉"付费"）；全部采纳修复。
  复审剩 2 处 MINOR（模型质量分支缺"结果可知"、"不得复制推导"范围被缩短），修复后按 reviewer 约定复跑检查即判 APPROVE。
- `agent_rules_gate` ok；`docs_contract_gate` passed；断言 `AGENTS.md` 的测试与 harness 测试组 361 passed。
- Harness focused（commit range `5d68c58..b020b11`）passed，receipt `.agent/harness/runs/20261029T012709106196Z/receipt.json`（gitignored，仅本地）。
  未跑 related/full。
- 已 push，远端 `main` = `b020b11098dbca1a955e28bd94c7224bf410418e`。
- 未在 Codex 运行时实际加载验证；仅静态确认前言写明 Codex 编排层为 OMX。

## Remaining Risks Or Next Work

- playbook（17681/18000 bytes）仍用 Codex 术语且接近上限，未处理；`CLAUDE.md` 映射表因此仍需保留。
- 未保存逐条新旧条款对照表；等价性证据仅为 reviewer 两轮结论与本节摘要。
- `work2` 的 OMC 问题在本会话后段已由用户修复（会话重启后 OMC agent 可用），未由本任务改动。

## Agent Guardrails

- 本次执行期间另一会话在共享 index 中暂存了 15 个路径。`git add` 会混入他人的暂存集；本次立即
  `git restore --staged` 撤回自己的路径，再用 `git commit --only <paths>` 提交，对方暂存数量保持 15。
- 有并发写入者时，`agent_harness.py inspect/verify --staged` 会把他人的暂存内容算进来；改用 commit range 取 receipt。
