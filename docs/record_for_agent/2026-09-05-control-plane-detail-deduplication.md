---
record_kind: session_summary
topic_id: control-plane-detail-deduplication
learning_eligibility: ineligible
---

# Control-Plane Detail Deduplication

Date: 2026-09-05

## Scope And Ownership

用户批准第一轮文档分层：精简逐 Shot Gate、实验优先级和 Learning/record 重复流程。
本轮只修改 root `AGENTS.md`、`.agent/context/control-plane-playbook.md`、本文与直接受影响的
2026-08-25 历史记录提示；不修改 Product Runtime、Skill、Provider 或 Harness policy。
全局自定义 subagent 路由继续由 `/home/reggie/.codex/AGENTS.md` 与 `agents/*.toml` 管理。

| Concern | Durable rule | Detailed owner |
| --- | --- | --- |
| Empirical priority | root 的 uncertainty distinction、适用条件、实验不等于 Production acceptance | playbook `Empirical Uncertainty Triage` 的场景、排除项、前置条件与操作顺序 |
| Per-Shot barrier | root 的 explicit MCP、exact bytes、required PASS、FAIL/NOT_EVALUATED 阻断及 local bounded/evidence-first repair | playbook `Per-Shot Post-Media Gate` 的预算、单变量、新 identity/intent/permit、完整重验和任务停止条件 |
| Learning | root 的自动 evaluation、advisory-only、保留 adopted claim、用户确认及 target owner verification | `distill-ai-video-learning/SKILL.md` 的字段、identity/admission、confirmation 与 adoption；playbook 只链接 |
| Session record | root 的 substantial stable-boundary 主动评估与 repository 外 effects | `record-ai-video-session/SKILL.md` 的 record/no-record、supersession、checkpoint 与 ACK；playbook 只链接 |

## Preserved Contracts

授权、secret、budget、egress、unknown-outcome fail-closed、唯一 committer、禁止自动 activation 与
P6/Final Acceptance 边界保持。Gate 本身不能重试；local bounded repair 仍由 orchestration 执行。
本次不修改 media Gate rubric 或把 media/engineering evidence 互相升级。

移除的 Learning/record 字段与状态表已存在于对应 Skill，没有创建第二 owner。
[旧记录](2026-08-25-control-plane-layering-and-session-record-gate.md) 保留历史 measurements，
只增加当前 owner 布局的更正提示。未顺带清理 playbook 的其他章节。

## Verification Boundary

Harness inspection 将 owned paths 路由到 `harness_control`、`documentation`、`open_video_skill`
与 `control_plane`，无 fallback。Exact staged Harness 的 254 项测试通过（boundary 2、Harness 205、
open-video 39、Seedance authoring 8），Architecture Gate 为 PASS 且无 findings，docs contract 和
policy audit 通过。最终 receipt：`.agent/harness/runs/control-plane-dedup-final-20260905/receipt.json`。
独立 `reviewer_xhigh` 未发现 blocking issue 或 material risk；审查仅覆盖本轮四个文档。
逐章节比较确认约定范围外的 root/playbook 章节原文未变，文档 local links/anchors 均可达。
本轮不执行 live Provider、媒体生成或产品质量验收。
既有前端及相关 Python/tests 的并发修改不属于本轮，保持在 verification snapshot 之外。

## Record And Learning Evaluation

按 `record-ai-video-session` 记录本次稳定的文档 owner 决策；按 `distill-ai-video-learning`
评估为 `no_candidate`。这是对既有契约的单次分层去重，没有新模型实验或需要更新的 adopted
Learning Claim，不创建占位 candidate，也不修改 Skill/Policy/Gate target。
记录过程不发 Provider/media call、不 push/release、不主动刷新 RAG index。
