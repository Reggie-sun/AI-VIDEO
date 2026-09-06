---
record_kind: session_summary
topic_id: operator-ceiling-renewal-policy
learning_eligibility: ineligible
---

# Operator Ceiling Renewal Policy

## User Intent And Change

用户因已授权 S01 生成被过期内部上限阻断，明确要求“把仓库规则改了”。本次修改
`AGENTS.md` 的 durable routing、playbook 的唯一续期流程及 `docs/vidu-provider.md` 的字段说明。
已授权任务可沿用既有纯 operator upper bound，保存真实续期决定、新旧 profile hash 和
剩余 quota，创建最多一小时的新 immutable profile，不再重复请求人工操作。

## Runtime Boundary

`ViduProviderProfile` 本来就是 dated operator cost ceiling；`ViduVideoProvider.preview`
仍检查当前时间位于有效窗口。没有修改 Product Runtime/schema、实际费率、reservation、
submit count、egress 或 permit，也没有覆盖历史 profile。真实市场 pricing snapshot 不适用。
新决定不是伪造市场观察，不能用新 profile 恢复旧 submit；新请求仍经过完整 canonical seam。

## Verification And Learning

文档 contract 与 policy audit 已通过；相关现有 tests 和 independent review 另按本轮输出报告。
用户禁止 worktree，未生成 detached-worktree Harness receipt，普通检查不冒充该 receipt。
自动学习评估 `no_candidate`：这是用户授权的 policy change，没有新增独立媒体实验。
保留所有其他 staged/dirty 文件；本 policy checkpoint 本身没有 Provider/media/secret 操作，
没有 push，没有另行刷新 RAG index。
