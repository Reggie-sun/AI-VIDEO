---
record_kind: session_summary
topic_id: agent-guide-context-loading
learning_eligibility: ineligible
---

# Agent Guide Context Loading

Date: 2026-09-23

## Scope And Ownership

本轮继续精简 root `AGENTS.md`，将逐项阅读顺序移至
`.agent/context/control-plane-playbook.md` 的 `Task Context Loading`。Root 保留长期有效的
authority、product invariants、唯一 owner、安全与授权门槛、workflow routing、verification 和
completion contract；playbook 仅是按 task concern 读取的 advisory operational reference。
当前实现、phase、surface map 与 changed-path checks 仍分别由 runtime baseline、roadmap、
contract matrix 与 Harness policy 管理。

## Session Work And Decisions

- Root `Read Order` 从逐项清单改为分层入口；本机 T8 操作、可选 handoff/bug-memory 和草稿的
  读取细节移至 playbook，读取后仍须以当前 code、tests、Git 和 runtime evidence 复核。
- 成片质量、Agent Memory/Learning、workflow review、Harness、paid Provider 与 local ComfyUI
  章节压缩重复叙述，保留原有 hard gates，并链接既有 playbook 或 Skill owner。
- `<!-- aoci:begin -->` 管理区、Product Runtime、Harness policy 与 Provider state 未修改。
  这次文档去重不产生新的执行授权或 runtime acceptance。

## Verification And Evidence

`python -m scripts.docs_contract_gate check` 和 `git diff --check` 在本轮文档改动后通过。
精确 staged snapshot 的最终 Harness receipt 由本轮交付单独报告。

AOCI `aoci_maintain` 在本轮因其他任务的 `observed_pending` scope 与 root `AGENTS.md`
的 `code_stale` 停止；未确认其他任务的 scope，也未修改认知 Entry。AOCI 对齐状态仍待对应
scope owner 处理后复核，不能把此记录视为索引已更新的证明。

按 `distill-ai-video-learning` 评估为 `no_candidate`：这是单次 control-plane 文档去重，
没有独立实验、受控对比或足以更新现有 Learning Claim 的新 evidence。

## Boundaries

本轮未执行 live Provider、媒体生成、Production state mutation、push 或 release。
`.codex/config.toml` 的本机路径配置与其他会话的 ecommerce plan/test 改动不属于本轮，
保持未 stage、未 commit。此记录是历史证据，不替代 root 契约或 executable truth。
