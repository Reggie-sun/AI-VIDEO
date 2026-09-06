# Paid Provider Price Research Policy Record

Date: 2026-09-06

## Supersession Notice

“过期 profile 一律阻塞”的 Agent-side 结论已由用户后续授权修改，见
[Operator Ceiling Renewal](../../.agent/context/control-plane-playbook.md#operator-ceiling-renewal)。
纯内部上限可在既有任务授权和剩余 quota 内重新确认；真实市场报价、runtime freshness、
旧提交恢复绑定和其他安全 Gate 不变。以下保留原 checkpoint 的历史描述。

## Purpose

本记录说明 Paid Provider 的 Agent-side bounded execution policy 已从“反复确认或研究价格”澄清为 task-level finite submit count。目标是阻止 Agent 为正常单次调用浏览官方 pricing、计算预计账单或刷新 pricing snapshot，同时保留当前 runtime 的安全与兼容边界。

## Current Policy Truth

Commit `b862a99` 更新 `AGENTS.md` 与 `.agent/context/control-plane-playbook.md`：

- 用户明确要求执行包含 remote/paid call 的任务时，授权继续按 accepted Provider、model、inputs 与完成目标所需的最少调用生效，不因付费反复询问。
- 用户未指定 submit count 时，Agent 按 accepted output 与 Shot 数量封存完成任务所需的最小 task-level ceiling。
- Agent 不得为了 authorization、submit ceiling 或单次调用准备而搜索官方当前单价、计算预计账单、刷新 pricing snapshot，或要求用户提供价格。
- task-level ceiling 耗尽、scope/provider/egress 变化、确需新增调用或上一次 outcome unknown 时，仍然停止并报告。

## Runtime Compatibility Boundary

本次只修改 Agent control-plane policy，没有迁移 Paid Provider runtime schema。

当前 `PaidProviderCallPreview`、`PaidProviderAuthorizationDecision` 与 `PaidProviderBudgetSnapshot` 仍保存 monetary upper bound、currency、reservation 与 settlement evidence；Provider profile 中既有 sealed operator upper bound 仍可由 runtime 消费。Agent 不得把这些内部值宣传为官方实际价格，也不得临时查价或伪造 observation/expiry 来修复 profile。

下列契约保持不变：

- exact request/preview binding；
- Cloud Egress 与 secret authorization；
- `ProductionStateCommitter` 先持久化 submit intent；
- committer-issued one-use permit；
- unknown outcome fail closed、禁止 blind retry/remint；
- historical monetary receipt、reopen、settlement 与 candidate validation semantics。

因此，文档中的 task-level submit count 是 Agent orchestration ceiling，不代表 current runtime monetary ledger 已成为 count-based schema。若已有 monetary profile 缺失或过期，Agent 必须报告 compatibility blocker，不能通过网络查价或虚构新值绕过。

## Verification And Review

变更 commit：`b862a99 docs: stop per-call provider price research`。

Exact commit-range Harness：

- receipt：`.agent/harness/runs/paid-price-research-policy-20260906/receipt.json`
- status：`passed`
- checks：documentation contract、policy audit、runtime/Skill boundary、Architecture Gate、Harness、`open-video` 与 `seedance-authoring`
- executable results：`2 passed`、`206 passed`、`39 passed`、`8 passed`
- receipt verification：integrity、freshness、snapshot、scope、policy 与 artifact checks 全部为 `true`

独立 `reviewer_xhigh` verdict 为 `accept`，没有 blocking issue 或 non-blocking concern。Review 特别确认文档未虚构 count-based runtime migration，也未放宽 Budget Guard、egress、secret、durable intent、one-use permit 或 unknown-outcome safety。

本次没有 Provider call、network pricing lookup、media generation、Manifest/Registry mutation、push 或 release。

## Remaining Risk

Seedance 与 Vidu preview 仍可能因 current monetary profile 的 freshness check fail closed。若未来产品要彻底移除 monetary dependency，并用 durable project/task submit quota 替代，必须作为独立的 versioned runtime migration 处理 Preview、Manifest、Reader、reservation、settlement、candidate validation 与 historical reopen；不得把本次 policy change 当成该 migration 已完成的证据。
