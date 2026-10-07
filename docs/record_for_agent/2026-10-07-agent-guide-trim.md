---
record_kind: session_summary
topic_id: agent-guide-trim
learning_eligibility: ineligible
---

# Agent Guide Trim

Date: 2026-10-07

## Scope

用户选择直接精简 `AGENTS.md`，保留重要约束，详细内容归现有 owner，并授权 commit/push。
基线 `31944ecdb5d4c257540452c298d320386a73d5c8`；本轮只改 root、playbook、路由定位测试和本记录。
没有 Product Runtime、Provider、媒体、预算、验收阈值、Harness policy 或正式 AOCI index 变更。

## Preservation Map

| Concern | Resident Contract | Detailed Owner |
| --- | --- | --- |
| Authority / ownership | 优先级、操作前按 concern 读取、唯一 committer/timeline/resolver | 既有 contract matrix；没有新建 owner catalog |
| Creative routing | 首次 authoring 前读路由和 matching Skill；live/paid preflight 缺失停止 | playbook `Creative Skill Routing And Preflight` 的既有 Skill Selection |
| Workflow / review | Native primary、authorized spec 自动 plan、tests/Harness 后 Risk Gate、Parent 裁决 | playbook `Workflow Selection` 接收原 T0–T3/bug 路由；`SUBAGENTS.md` 继续独占 delegation/review 细则 |
| AOCI / CodeGraph | 结构任务触发、简单任务不机械调用、advisory-only | 原 AOCI 操作段落迁到 playbook `Cognition Tools`，维护仍由官方 MCP 流程拥有 |
| Verification | exact snapshot/range、fresh receipt、unmapped fallback、不能外推 acceptance | playbook 保留 scope/policy/artifact hashes/freshness、rules/invariant 检查说明；checks/argv 仍归原 Harness |
| Media / effect safety | 逐 Shot explicit MCP、required PASS、NOT_EVALUATED/unknown 停止、有限 repair、凭据和 paid/local 授权 | 既有 Per-Shot/Provider/Pilot 章节；没有放宽授权或门槛 |
| Completion / learning | stable record、自动 learning evaluation、确认前不 adoption、每次 commit 后 push 并验 SHA | 原 record/learning Skills |

`.agent/context/` 不拥有 runtime truth 或额外授权；root 明确委托的操作流程必须执行。
不使用“advisory”把原本 required 的 preflight/Gate 变为可选。

## Size And Verification

`AGENTS.md`：180 → 109 行，13990 → 11481 UTF-8 bytes，常驻字节减少约 18%。
Playbook：203 → 209 行，16059 → 17772 bytes；两者合计减少 796 bytes。行数减少不能冒充同等 token 节省。
现有文档预算未提高，新链接/anchors 由现有 rule gate 检查。

首次 Harness 在 Seedance 测试失败：旧断言要求 root 存在完整路由表。
调整后同时检查 root 的操作前读取要求、creative 链接及 authoring 时机，以及 playbook 的 selected Seedance、Non-Seedance/higgsfield 和 retired dispatch 边界；不删除路由保护。
定向 8 tests 通过；候选 snapshot `ada46975414410c9efec1f5f380d5e845ece5f5d` 的 Harness
`.agent/harness/runs/guide-trim-candidate-20261007/receipt.json` 全部通过，377 tests，Architecture Gate 无 findings。
最终含本记录的 publication snapshot 另由 `.agent/harness/runs/guide-trim-publish-20261007/receipt.json` 核验。

## Review And Evidence Boundary

独立工作单元为只读规则保留核对，使用 `external-subagent` 的 sealed Kimi `deep` route；不授权 writer 或 nested delegation。
Invocation `640ab88b-18c1-4adf-b3d8-3150ec07cd71`，canonical receipt 位于
`/home/reggie/.local/state/agent-subagent-router/runs/640ab88b-18c1-4adf-b3d8-3150ec07cd71/invocation-receipt.json`。
Requested `k3[1m] / max`，actual wire `k3 / max`，3 requests 均 `IDENTITY_VERIFIED`；process exit 0、protocol `PARSED`，不是 acceptance。
Parent 重算全部 artifact 和 evidence_ref hashes，确认旧文档来自基线、审查包与候选 root/playbook bytes 一致。
审查发现“额外 reviewer 仅按用户新的明确要求”在压缩时遗漏：`CONFIRMED`，恢复原句；同时恢复原 constitution 自述和“低位阶不得覆盖高位阶”。Parent 另把 `run` 的 atomic 表述还原为仅描述 Manifest 持久化。
这些是旧规则原文恢复，无新增授权、流程或 runtime 语义；未声称 Kimi 审过恢复后的 bytes，最终验证覆盖修正版。
定位测试的内存 mutation 检查也已实际执行：移除 root pointer、Seedance owner、Non-Seedance boundary 各自都触发 AssertionError。
Implementation Risk Gate：候选 tree 如上，用户未要求 implementation review；无新增 effectful runtime、credential/authority/持久化实现路径，测试只迁移文档定位断言并加强读取入口检查；无 critical consequence 或重大剩余 runtime gap，结果 `KIMI_REVIEW_NOT_REQUIRED`。本次 Kimi 是独立文档保留核对，不叠加 reviewer。
最终技术判断归 Parent；结构/测试证据不证明未来 Agent 一定遵守自然语言，也不证明媒体质量。

## Record And Learning Evaluation

按 `record-ai-video-session` 记录；按 `distill-ai-video-learning` 评估为 `no_candidate`。
这是既有约束的文档去重及定位测试调整，没有模型质量实验、controlled arms 或需更新的 Learning Claim；不创建占位候选。
历史治理记录描述各自 checkpoint，不重写历史 measurements。未刷新 RAG index；没有 Product Provider 调用或媒体生成。
