---
record_kind: architecture_implementation
topic_id: agents-constitution-routing
learning_eligibility: ineligible
---

# AGENTS Constitution Routing Phase 1 Record

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

## Remaining Risks Or Next Work

- 第 2 步（未做）：`AGENTS.md` 改用中性运行时术语，缩短 `CLAUDE.md` 映射表；Codex 直接读取 `AGENTS.md`，两侧都需验证。
- 第 3 步（未做）：剩余各节改为"做什么 + 为什么"的白话；保持 14000 bytes 上限不变。
- 以下测试按原文断言 `AGENTS.md`，改写措辞时需同步：`test_distill_ai_video_learning_skill.py`（Completion Standard）、
  `test_seedance_authoring_skill.py`（Task Routing 两句）、`test_ecommerce_ad_workflow_skill.py`（Per-Shot Gate）。
- playbook 也已接近上限，规则无法改搬进 playbook；新家只能是按需加载的 Skill 或 docs。
- OMC 在 `work2` 不可用的问题仍未处理。

## Agent Guardrails

- 本次执行期间另一会话在共享 index 中暂存了 15 个路径。`git add` 会混入他人的暂存集；本次立即
  `git restore --staged` 撤回自己的路径，再用 `git commit --only <paths>` 提交，对方暂存数量保持 15。
- 有并发写入者时，`agent_harness.py inspect/verify --staged` 会把他人的暂存内容算进来；改用 commit range 取 receipt。
